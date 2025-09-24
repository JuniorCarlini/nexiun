import json
from decimal import Decimal
from users.models import User
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, date
from projects.models import Project, Bank, CreditLine
from django.shortcuts import render, redirect
from enterprises.models import InternalMessage, Client
from units.models import Unit, BankAccount, Transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q, Value, DecimalField, Avg
from django.db.models.functions import Coalesce, TruncMonth, ExtractMonth, ExtractYear

# Importar funções de filtro do módulo reports
from reports.utils import (
    get_user_accessible_units,
    get_user_accessible_projects,
    get_user_accessible_clients,
    filter_queryset_by_user_units
)

@login_required
def home(request):
    """View principal - Dashboard CEO/Diretor com filtros por permissões"""
    user = request.user
    enterprise = user.enterprise
    
    # Verificar se é aniversário do usuário
    today = timezone.now().date()
    is_birthday = False
    if user.date_of_birth:
        is_birthday = (user.date_of_birth.month == today.month and 
                      user.date_of_birth.day == today.day)
    
    # ============ MÉTRICAS PRINCIPAIS COM FILTROS DE PERMISSÃO ============
    
    # Obter projetos base da empresa
    base_projects = Project.objects.filter(
        enterprise=enterprise,
        is_active=True
    )
    
    # Filtrar projetos baseado nas permissões do usuário
    accessible_projects = get_user_accessible_projects(user, base_projects)
    
    # 1. Faturamento Total (soma dos valores dos projetos aprovados/liberados)
    faturamento_total = accessible_projects.filter(
        status__in=['AP', 'AF', 'FM', 'LB', 'RC']  # Projetos que geram faturamento
    ).aggregate(total=Coalesce(Sum('value'), Decimal('0')))['total']
    
    # 2. Total de Projetos em Andamento (todos os status ativos exceto finalizados)
    projetos_andamento = accessible_projects.filter(
        status__in=['AC', 'PE', 'AN', 'AP', 'AF', 'FM', 'LB']  # Não inclui 'RC' (finalizado)
    ).count()
    
    # 3. Total de Unidades Ativas (baseado nas permissões do usuário)
    accessible_units = get_user_accessible_units(user)
    total_unidades = accessible_units.count()
    
    # 4. Total de Clientes Ativos (baseado nas permissões do usuário)
    base_clients = Client.objects.filter(
        enterprise=enterprise,
        status='ATIVO',
        is_active=True
    )
    accessible_clients = get_user_accessible_clients(user, base_clients)
    clientes_ativos = accessible_clients.count()
    
    # ============ DADOS PARA GRÁFICO DE BARRAS - UNIDADES (COM FILTROS) ============
    
    # Obter dados mensais dos últimos 6 meses por unidade (apenas unidades acessíveis)
    six_months_ago = today - timedelta(days=180)
    
    # Projetos dos últimos 6 meses agrupados por unidade e mês (filtrados)
    unidades_data = accessible_projects.filter(
        created_at__date__gte=six_months_ago
    ).annotate(
        year=ExtractYear('created_at'),
        month=ExtractMonth('created_at')
    ).values('unit__name', 'year', 'month').annotate(
        total_value=Sum('value'),
        project_count=Count('id')
    ).order_by('unit__name', 'year', 'month')
    
    # Organizar dados para o gráfico de barras
    unidades_chart_data = {}
    months_set = set()
    
    for item in unidades_data:
        unit_name = item['unit__name']
        month_key = f"{item['year']}-{item['month']:02d}"
        months_set.add(month_key)
        
        if unit_name not in unidades_chart_data:
            unidades_chart_data[unit_name] = {}
        
        unidades_chart_data[unit_name][month_key] = float(item['total_value'] or 0)
    
    # Preparar dados para ApexCharts
    months_list = sorted(list(months_set))
    unidades_series = []
    
    for unit_name, monthly_data in unidades_chart_data.items():
        series_data = []
        for month in months_list:
            series_data.append(monthly_data.get(month, 0))
        
        unidades_series.append({
            'name': unit_name,
            'data': series_data
        })
    
    # Formataar meses para exibição
    months_labels = []
    for month in months_list:
        year, month_num = month.split('-')
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                      'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        months_labels.append(f"{month_names[int(month_num)-1]} {year}")
    
    # ============ DADOS PARA GRÁFICO DONUT - LINHAS DE CRÉDITO (COM FILTROS) ============
    
    # Contar projetos por linha de crédito (top 5) - apenas projetos acessíveis
    credito_data = accessible_projects.values('credit_line__name').annotate(
        project_count=Count('id')
    ).order_by('-project_count')[:5]  # Limitar a 5 para melhor visualização
    
    # Preparar dados para o gráfico donut
    credito_labels = []
    credito_values = []
    
    for item in credito_data:
        if item['credit_line__name']:  # Verificar se não é None
            credito_labels.append(item['credit_line__name'])
            credito_values.append(item['project_count'])
    
    # ============ DADOS PARA GRÁFICO DONUT - BANCOS (COM FILTROS) ============
    
    # Contar projetos por banco (top 5) - apenas projetos acessíveis
    bancos_data = accessible_projects.values('bank__name').annotate(
        project_count=Count('id')
    ).order_by('-project_count')[:5]  # Limitar a 5 para melhor visualização
    
    # Preparar dados para o gráfico donut de bancos
    bancos_labels = []
    bancos_values = []
    
    for item in bancos_data:
        if item['bank__name']:  # Verificar se não é None
            bancos_labels.append(item['bank__name'])
            bancos_values.append(item['project_count'])
    
    # ============ MENSAGENS (COM FILTROS) ============
    
    # Obter mensagens internas recentes (filtradas por unidades acessíveis)
    messages_queryset = InternalMessage.objects.filter(enterprise=enterprise)
    
    # Se o usuário tem acesso limitado a unidades específicas
    user_units = user.units.all()
    user_role_codes = list(user.roles.filter(is_active=True).values_list('code', flat=True))
    restricted_roles = ['socio_unidade', 'franqueado', 'gerente', 'projetista', 'captador']
    
    # Se o usuário tem cargo restrito, filtrar mensagens
    if any(role in restricted_roles for role in user_role_codes) and user_units.exists():
        messages_queryset = messages_queryset.filter(
            Q(scope='unit', unit__in=user_units) | Q(scope='enterprise')
        )
    
    mensagens = messages_queryset.order_by('-date')[:5]
    
    # ============ CONTEXT PARA O TEMPLATE ============
    
    context = {
        # Dados do usuário
        'is_birthday': is_birthday,
        
        # Métricas principais (filtradas)
        'faturamento_total': faturamento_total,
        'projetos_andamento': projetos_andamento,
        'total_unidades': total_unidades,
        'clientes_ativos': clientes_ativos,
        
        # Dados para gráfico de barras (unidades acessíveis)
        'unidades_series': json.dumps(unidades_series),
        'meses_labels': json.dumps(months_labels),
        
        # Dados para gráfico donut (linhas de crédito - filtrados)
        'credito_labels': json.dumps(credito_labels),
        'credito_values': json.dumps(credito_values),
        
        # Dados para gráfico donut (bancos - filtrados)
        'bancos_labels': json.dumps(bancos_labels),
        'bancos_values': json.dumps(bancos_values),
        
        # Mensagens (filtradas)
        'mensagens': mensagens,
        
        # Dados da empresa
        'enterprise': enterprise,
        
        # Informação adicional para debug
        'user_accessible_units': accessible_units.count(),
        'user_role_codes': user_role_codes,
    }
    
    return render(request, 'home/home.html', context)
