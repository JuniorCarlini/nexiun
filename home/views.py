import json
from decimal import Decimal
from users.models import User
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, date
from projects.models import Project, Bank
from django.shortcuts import render, redirect
from enterprises.models import InternalMessage
from units.models import Unit, BankAccount, Transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q, Value, DecimalField, Avg
from django.db.models.functions import Coalesce, TruncMonth, ExtractMonth, ExtractYear

@login_required
def home(request):
    """View principal"""
    user = request.user
    
    # Filtrar contas bancárias baseado na unidade do usuário
    contas_bancarias = BankAccount.objects.filter(unit__enterprise=user.enterprise)
    if user.unit and user.has_perm('users.view_unit_dashboard') and not user.has_perm('users.view_company_dashboard'):
        contas_bancarias = contas_bancarias.filter(unit=user.unit)
    
    # Calcular saldo total atual
    saldo_atual = sum(conta.get_current_balance() for conta in contas_bancarias)
    
    # Obter transações do mês atual
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    transactions_filter = {'date__gte': start_of_month, 'date__lte': today}
    if user.unit and user.has_perm('users.view_unit_dashboard') and not user.has_perm('users.view_company_dashboard'):
        transactions_filter['bank_account__unit'] = user.unit
    else:
        transactions_filter['bank_account__unit__enterprise'] = user.enterprise
    
    current_month_transactions = Transaction.objects.filter(**transactions_filter)
    
    # Calcular entradas e saídas do mês atual
    current_month_entradas = current_month_transactions.filter(category='entrada').aggregate(
        total=Coalesce(Sum('amount'), Decimal('0')))['total']
    current_month_saidas = current_month_transactions.filter(category='saida').aggregate(
        total=Coalesce(Sum('amount'), Decimal('0')))['total']
    
    # Saldo líquido do mês
    current_month_liquido = current_month_entradas - current_month_saidas
    
    # Dados para gráfico de fluxo de caixa dos últimos 6 meses
    six_months_ago = today - timedelta(days=180)
    
    # Transações dos últimos 6 meses
    transactions_6m_filter = {'date__gte': six_months_ago, 'date__lte': today}
    if user.unit and user.has_perm('users.view_unit_dashboard') and not user.has_perm('users.view_company_dashboard'):
        transactions_6m_filter['bank_account__unit'] = user.unit
    else:
        transactions_6m_filter['bank_account__unit__enterprise'] = user.enterprise
    
    transactions_6m = Transaction.objects.filter(**transactions_6m_filter)
    
    # Agrupar por mês
    monthly_data = transactions_6m.annotate(
        year=ExtractYear('date'),
        month=ExtractMonth('date')
    ).values('year', 'month', 'category').annotate(
        total=Sum('amount')
    ).order_by('year', 'month')
    
    # Organizar dados para o gráfico
    chart_data = {}
    for item in monthly_data:
        month_key = f"{item['year']}-{item['month']:02d}"
        if month_key not in chart_data:
            chart_data[month_key] = {'entradas': 0, 'saidas': 0}
        
        if item['category'] == 'entrada':
            chart_data[month_key]['entradas'] = float(item['total'])
        else:
            chart_data[month_key]['saidas'] = float(item['total'])
    
    # Converter para listas ordenadas para o JavaScript
    months = sorted(chart_data.keys())
    entradas_data = [chart_data[month]['entradas'] for month in months]
    saidas_data = [chart_data[month]['saidas'] for month in months]
    
    # Formataar meses para exibição
    months_labels = []
    for month in months:
        year, month_num = month.split('-')
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                      'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        months_labels.append(f"{month_names[int(month_num)-1]} {year}")
    
    # Obter mensagens internas recentes
    messages_queryset = InternalMessage.objects.filter(enterprise=user.enterprise)
    if user.unit and user.has_perm('users.view_unit_dashboard') and not user.has_perm('users.view_company_dashboard'):
        # Se usuário só pode ver dados da unidade, filtra por mensagens da unidade ou corporativas
        messages_queryset = messages_queryset.filter(
            Q(scope='unit', unit=user.unit) | Q(scope='enterprise')
        )
    
    recent_messages = messages_queryset.order_by('-date')[:5]
    
    context = {
        'saldo_atual': saldo_atual,
        'current_month_entradas': current_month_entradas,
        'current_month_saidas': current_month_saidas,
        'current_month_liquido': current_month_liquido,
        'recent_messages': recent_messages,
        'months_labels': json.dumps(months_labels),
        'entradas_data': json.dumps(entradas_data),
        'saidas_data': json.dumps(saidas_data),
    }
    
    return render(request, 'home/home.html', context)
