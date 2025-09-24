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

# Importar funções de filtro do core.mixins (mesmo sistema usado em users)
from core.mixins import (
    get_selected_unit_from_request, 
    is_all_units_selected_from_request,
    get_accessible_units_from_request
)

@login_required
def home(request):
    """View principal - Dashboard CEO/Diretor com filtros por sessões (mesmo sistema de users)"""
    user = request.user
    enterprise = user.enterprise
    
    # Verificar se é aniversário do usuário
    today = timezone.now().date()
    is_birthday = False
    if user.date_of_birth:
        is_birthday = (user.date_of_birth.month == today.month and 
                      user.date_of_birth.day == today.day)
    
    # ============ SISTEMA DE FILTROS POR SESSÃO (IGUAL AO USERS) ============
    
    # Verificar se está selecionado "Todas as unidades"
    is_all_units_selected = is_all_units_selected_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    accessible_units = get_accessible_units_from_request(request)
    
    # ============ FILTRAR DADOS BASEADO NA SESSÃO ============
    
    # Projetos base da empresa
    base_projects = Project.objects.filter(
        enterprise=enterprise,
        is_active=True
    )
    
    # Aplicar filtros baseado na seleção da sessão
    if is_all_units_selected:
        # "Todas as unidades" selecionado
        if user.has_perm('users.view_all_units'):
            # Pode ver todos os projetos da empresa
            filtered_projects = base_projects
        else:
            # Usuário normal - filtrar pelas suas unidades vinculadas
            user_units = user.units.all()
            if user_units.exists():
                filtered_projects = base_projects.filter(unit__in=user_units)
            else:
                filtered_projects = base_projects.none()
    else:
        # Unidade específica selecionada ou padrão
        if selected_unit:
            # Filtrar pela unidade específica selecionada
            if user.has_perm('users.view_all_units'):
                # Pode ver todos os projetos da unidade
                filtered_projects = base_projects.filter(unit=selected_unit)
            elif user.units.filter(id=selected_unit.id).exists():
                # Pode ver projetos da unidade se tiver acesso a ela
                filtered_projects = base_projects.filter(unit=selected_unit)
            else:
                # Não tem acesso à unidade selecionada
                filtered_projects = base_projects.none()
        else:
            # Nenhuma unidade selecionada - mostrar baseado nas permissões
            if user.has_perm('users.view_all_units'):
                # Pode ver todos os projetos da empresa
                filtered_projects = base_projects
            else:
                user_units = user.units.all()
                if user_units.exists():
                    filtered_projects = base_projects.filter(unit__in=user_units)
                else:
                    filtered_projects = base_projects.none()
    
    # ============ MÉTRICAS PRINCIPAIS COM FILTROS DE SESSÃO ============
    
    # 1. Faturamento Total (soma dos valores dos projetos aprovados/liberados)
    faturamento_total = filtered_projects.filter(
        status__in=['AP', 'AF', 'FM', 'LB', 'RC']  # Projetos que geram faturamento
    ).aggregate(total=Coalesce(Sum('value'), Decimal('0')))['total']
    
    # 2. Total de Projetos em Andamento (todos os status ativos exceto finalizados)
    projetos_andamento = filtered_projects.filter(
        status__in=['AC', 'PE', 'AN', 'AP', 'AF', 'FM', 'LB']  # Não inclui 'RC' (finalizado)
    ).count()
    
    # 3. Total de Unidades Ativas (baseado nas permissões do usuário)
    total_unidades = accessible_units.count()
    
    # 4. Total de Clientes Ativos (baseado nas unidades filtradas)
    if is_all_units_selected:
        if user.has_perm('users.view_all_units'):
            # Pode ver todos os clientes da empresa
            filtered_clients = Client.objects.filter(enterprise=enterprise, status='ATIVO', is_active=True)
        else:
            # Filtrar pelos clientes das unidades do usuário
            user_units = user.units.all()
            filtered_clients = Client.objects.filter(
                enterprise=enterprise, 
                status='ATIVO', 
                is_active=True,
                units__in=user_units
            ).distinct()
    else:
        if selected_unit:
            # Filtrar pelos clientes da unidade selecionada
            filtered_clients = Client.objects.filter(
                enterprise=enterprise, 
                status='ATIVO', 
                is_active=True,
                units=selected_unit
            )
        else:
            # Padrão baseado nas permissões
            if user.has_perm('users.view_all_units'):
                filtered_clients = Client.objects.filter(enterprise=enterprise, status='ATIVO', is_active=True)
            else:
                user_units = user.units.all()
                filtered_clients = Client.objects.filter(
                    enterprise=enterprise, 
                    status='ATIVO', 
                    is_active=True,
                    units__in=user_units
                ).distinct()
    
    clientes_ativos = filtered_clients.count()
    
    # ============ DADOS PARA GRÁFICO DE BARRAS - UNIDADES (COM FILTROS) ============
    
    # Obter dados mensais dos últimos 6 meses por unidade (apenas unidades filtradas)
    six_months_ago = today - timedelta(days=180)
    
    # Projetos dos últimos 6 meses agrupados por unidade e mês (filtrados)
    unidades_data = filtered_projects.filter(
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
    
    # Contar projetos por linha de crédito (top 5) - apenas projetos filtrados
    credito_data = filtered_projects.values('credit_line__name').annotate(
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
    
    # Contar projetos por banco (top 5) - apenas projetos filtrados
    bancos_data = filtered_projects.values('bank__name').annotate(
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
    
    # Obter mensagens internas recentes (filtradas por unidades da sessão)
    messages_queryset = InternalMessage.objects.filter(enterprise=enterprise)
    
    # Aplicar filtros de mensagens baseado na seleção da sessão
    if is_all_units_selected:
        if not user.has_perm('users.view_all_units'):
            # Usuário normal - filtrar por mensagens das suas unidades ou corporativas
            user_units = user.units.all()
            if user_units.exists():
                messages_queryset = messages_queryset.filter(
                    Q(scope='unit', unit__in=user_units) | Q(scope='enterprise')
                )
    else:
        if selected_unit and not user.has_perm('users.view_all_units'):
            # Filtrar por mensagens da unidade selecionada ou corporativas
            messages_queryset = messages_queryset.filter(
                Q(scope='unit', unit=selected_unit) | Q(scope='enterprise')
            )
    
    mensagens = messages_queryset.order_by('-date')[:5]
    
    # ============ CONTEXT PARA O TEMPLATE ============
    
    context = {
        # Dados do usuário
        'is_birthday': is_birthday,
        
        # Métricas principais (filtradas por sessão)
        'faturamento_total': faturamento_total,
        'projetos_andamento': projetos_andamento,
        'total_unidades': total_unidades,
        'clientes_ativos': clientes_ativos,
        
        # Dados para gráfico de barras (unidades filtradas)
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
        
        # Informações da sessão para debug
        'is_all_units_selected': is_all_units_selected,
        'selected_unit': selected_unit,
        'accessible_units_count': accessible_units.count(),
    }
    
    return render(request, 'home/home.html', context)
