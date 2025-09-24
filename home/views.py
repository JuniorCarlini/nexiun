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

@login_required
def home(request):
    """View principal - Dashboard CEO/Diretor"""
    user = request.user
    enterprise = user.enterprise
    
    # Verificar se é aniversário do usuário
    today = timezone.now().date()
    is_birthday = False
    if user.date_of_birth:
        is_birthday = (user.date_of_birth.month == today.month and 
                      user.date_of_birth.day == today.day)
    
    # ============ MÉTRICAS PRINCIPAIS CEO/DIRETOR ============
    
    # 1. Faturamento Total (soma dos valores dos projetos aprovados/liberados)
    faturamento_total = Project.objects.filter(
        enterprise=enterprise,
        status__in=['AP', 'AF', 'FM', 'LB', 'RC'],  # Projetos que geram faturamento
        is_active=True
    ).aggregate(total=Coalesce(Sum('value'), Decimal('0')))['total']
    
    # 2. Total de Projetos em Andamento (todos os status ativos exceto finalizados)
    projetos_andamento = Project.objects.filter(
        enterprise=enterprise,
        status__in=['AC', 'PE', 'AN', 'AP', 'AF', 'FM', 'LB'],  # Não inclui 'RC' (finalizado)
        is_active=True
    ).count()
    
    # 3. Total de Unidades Ativas
    total_unidades = Unit.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).count()
    
    # 4. Total de Clientes Ativos
    clientes_ativos = Client.objects.filter(
        enterprise=enterprise,
        status='ATIVO',
        is_active=True
    ).count()
    
    # ============ DADOS PARA GRÁFICO DE BARRAS - UNIDADES ============
    
    # Obter dados mensais dos últimos 6 meses por unidade
    six_months_ago = today - timedelta(days=180)
    
    # Projetos dos últimos 6 meses agrupados por unidade e mês
    unidades_data = Project.objects.filter(
        enterprise=enterprise,
        created_at__date__gte=six_months_ago,
        is_active=True
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
    
    # ============ DADOS PARA GRÁFICO DONUT - LINHAS DE CRÉDITO ============
    
    # Contar projetos por linha de crédito (top 5)
    credito_data = Project.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).values('credit_line__name').annotate(
        project_count=Count('id')
    ).order_by('-project_count')[:5]  # Limitar a 5 para melhor visualização
    
    # Preparar dados para o gráfico donut
    credito_labels = []
    credito_values = []
    
    for item in credito_data:
        if item['credit_line__name']:  # Verificar se não é None
            credito_labels.append(item['credit_line__name'])
            credito_values.append(item['project_count'])
    
    # ============ DADOS PARA GRÁFICO DONUT - BANCOS ============
    
    # Contar projetos por banco (top 5)
    bancos_data = Project.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).values('bank__name').annotate(
        project_count=Count('id')
    ).order_by('-project_count')[:5]  # Limitar a 5 para melhor visualização
    
    # Preparar dados para o gráfico donut de bancos
    bancos_labels = []
    bancos_values = []
    
    for item in bancos_data:
        if item['bank__name']:  # Verificar se não é None
            bancos_labels.append(item['bank__name'])
            bancos_values.append(item['project_count'])
    
    # ============ MENSAGENS (MANTER IGUAL) ============
    
    # Obter mensagens internas recentes
    mensagens = InternalMessage.objects.filter(
        enterprise=enterprise
    ).order_by('-date')[:5]
    
    # ============ CONTEXT PARA O TEMPLATE ============
    
    context = {
        # Dados do usuário
        'is_birthday': is_birthday,
        
        # Métricas principais
        'faturamento_total': faturamento_total,
        'projetos_andamento': projetos_andamento,
        'total_unidades': total_unidades,
        'clientes_ativos': clientes_ativos,
        
        # Dados para gráfico de barras (unidades)
        'unidades_series': json.dumps(unidades_series),
        'meses_labels': json.dumps(months_labels),
        
        # Dados para gráfico donut (linhas de crédito)
        'credito_labels': json.dumps(credito_labels),
        'credito_values': json.dumps(credito_values),
        
        # Dados para gráfico donut (bancos)
        'bancos_labels': json.dumps(bancos_labels),
        'bancos_values': json.dumps(bancos_values),
        
        # Mensagens
        'mensagens': mensagens,
        
        # Dados da empresa
        'enterprise': enterprise,
    }
    
    return render(request, 'home/home.html', context)
