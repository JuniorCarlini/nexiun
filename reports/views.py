from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from users.decorators import permission_required
from users.models import User
from projects.models import Project, ProjectHistory, Bank, CreditLine
from enterprises.models import Client
from units.models import Unit, Transaction
from .models import ReportCache, ReportSettings
from .utils import (
    calculate_approval_time, 
    calculate_conversion_rates,
    generate_performance_metrics,
    export_to_excel,
    export_to_pdf
)


# ==================== DASHBOARD PRINCIPAL ====================

@login_required
def reports_dashboard_view(request):
    """Dashboard principal com visão geral dos indicadores"""
    user = request.user
    enterprise = user.enterprise
    
    # Filtros de período
    period_days = request.GET.get('period', 365)
    try:
        period_days = int(period_days)
    except ValueError:
        period_days = 365
    
    start_date = timezone.now().date() - timedelta(days=period_days)
    
    # Indicadores principais
    total_projects = Project.objects.filter(
        enterprise=enterprise,
        created_at__date__gte=start_date,
        is_active=True
    ).count()
    
    approved_projects = Project.objects.filter(
        enterprise=enterprise,
        status__in=['AP', 'AF', 'FM', 'LB', 'RC'],
        created_at__date__gte=start_date,
        is_active=True
    ).count()
    
    approval_rate = (approved_projects / total_projects * 100) if total_projects > 0 else 0
    
    # Tempo médio de aprovação
    avg_approval_time = calculate_approval_time(enterprise, start_date)
    
    # Taxa de retrabalho
    rework_count = ProjectHistory.objects.filter(
        project__enterprise=enterprise,
        timestamp__date__gte=start_date,
        changes__status__isnull=False
    ).values_list('project_id', flat=True).distinct().count()
    
    rework_rate = (rework_count / total_projects * 100) if total_projects > 0 else 0
    
    # Clientes ativos
    active_clients = Client.objects.filter(
        enterprise=enterprise,
        status='ATIVO',
        is_active=True
    ).count()
    
    # Top 5 bancos
    top_banks = Bank.objects.filter(
        enterprise=enterprise,
        projects__created_at__date__gte=start_date
    ).annotate(
        project_count=Count('projects')
    ).order_by('-project_count')[:5]
    
    # Top 5 unidades
    top_units = Unit.objects.filter(
        enterprise=enterprise,
        projects__created_at__date__gte=start_date
    ).annotate(
        project_count=Count('projects'),
        total_value=Sum('projects__value')
    ).order_by('-project_count')[:5]
    
    context = {
        'total_projects': total_projects,
        'approved_projects': approved_projects,
        'approval_rate': round(approval_rate, 1),
        'avg_approval_time': avg_approval_time,
        'rework_rate': round(rework_rate, 1),
        'active_clients': active_clients,
        'top_banks': top_banks,
        'top_units': top_units,
        'period_days': period_days,
    }
    
    return render(request, 'reports/dashboard.html', context)


# ==================== RELATÓRIOS DE OPERAÇÕES ====================

@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def operations_performance_view(request):
    """Relatório de performance das operações"""
    user = request.user
    enterprise = user.enterprise
    
    # Filtros
    period_days = int(request.GET.get('period', 365))
    unit_id = request.GET.get('unit')
    bank_id = request.GET.get('bank')
    
    start_date = timezone.now().date() - timedelta(days=period_days)
    
    # Query base
    projects_query = Project.objects.filter(
        enterprise=enterprise,
        created_at__date__gte=start_date,
        is_active=True
    )
    
    if unit_id:
        projects_query = projects_query.filter(unit_id=unit_id)
    if bank_id:
        projects_query = projects_query.filter(bank_id=bank_id)
    
    # Métricas por status
    status_metrics = projects_query.values('status').annotate(
        count=Count('id'),
        total_value=Sum('value')
    ).order_by('status')
    
    # Propostas por linha de crédito
    credit_line_metrics = projects_query.values(
        'credit_line__name',
        'credit_line__type_credit'
    ).annotate(
        count=Count('id'),
        total_value=Sum('value')
    ).order_by('-count')
    
    # Propostas por banco
    bank_metrics = projects_query.values(
        'bank__name'
    ).annotate(
        count=Count('id'),
        total_value=Sum('value')
    ).order_by('-count')
    
    # Filtros para o template
    units = Unit.objects.filter(enterprise=enterprise, is_active=True)
    banks = Bank.objects.filter(enterprise=enterprise, is_active=True)
    
    context = {
        'status_metrics': status_metrics,
        'credit_line_metrics': credit_line_metrics,
        'bank_metrics': bank_metrics,
        'units': units,
        'banks': banks,
        'selected_unit': unit_id,
        'selected_bank': bank_id,
        'period_days': period_days,
    }
    
    return render(request, 'reports/operations/performance.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def operations_timing_view(request):
    """Análise detalhada de tempo de aprovação"""
    user = request.user
    enterprise = user.enterprise
    
    # Calcular tempos por fase usando o histórico
    timing_data = calculate_approval_time(enterprise, detailed=True)
    
    context = {
        'timing_data': timing_data,
    }
    
    return render(request, 'reports/operations/timing.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def operations_by_bank_view(request):
    """Relatório detalhado por banco"""
    user = request.user
    enterprise = user.enterprise
    
    bank_performance = generate_performance_metrics(enterprise, group_by='bank')
    
    context = {
        'bank_performance': bank_performance,
    }
    
    return render(request, 'reports/operations/by_bank.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def operations_by_credit_line_view(request):
    """Relatório detalhado por linha de crédito"""
    user = request.user
    enterprise = user.enterprise
    
    credit_line_performance = generate_performance_metrics(enterprise, group_by='credit_line')
    
    context = {
        'credit_line_performance': credit_line_performance,
    }
    
    return render(request, 'reports/operations/by_credit_line.html', context)


# ==================== RELATÓRIOS DE CLIENTES ====================

@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def clients_indicators_view(request):
    """Indicadores gerais de clientes"""
    user = request.user
    enterprise = user.enterprise
    
    # Contadores por status
    clients_by_status = Client.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).values('status').annotate(count=Count('id'))
    
    # Taxa de recompra
    clients_with_multiple_projects = Client.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).annotate(
        project_count=Count('projects')
    ).filter(project_count__gt=1)
    
    total_active_clients = Client.objects.filter(
        enterprise=enterprise,
        status='ATIVO',
        is_active=True
    ).count()
    
    repurchase_rate = (
        clients_with_multiple_projects.count() / total_active_clients * 100
    ) if total_active_clients > 0 else 0
    
    # Detalhamento por unidade
    units_metrics = Unit.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).annotate(
        total_clients=Count('clients'),
        active_clients=Count('clients', filter=Q(clients__status='ATIVO'))
    )
    
    # Calcular clientes de recompra manualmente para cada unidade
    units_with_repurchase = []
    for unit in units_metrics:
        # Buscar clientes da unidade que têm mais de um projeto
        repurchase_clients_count = Client.objects.filter(
            units=unit,
            enterprise=enterprise,
            is_active=True
        ).annotate(
            project_count=Count('projects')
        ).filter(project_count__gt=1).count()
        
        # Adicionar o campo calculado
        unit.repurchase_clients = repurchase_clients_count
        units_with_repurchase.append(unit)
    
    context = {
        'clients_by_status': clients_by_status,
        'repurchase_rate': round(repurchase_rate, 1),
        'units_metrics': units_with_repurchase,
        'total_active_clients': total_active_clients,
    }
    
    return render(request, 'reports/clients/indicators.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def clients_conversion_view(request):
    """Análise de funil de conversão"""
    user = request.user
    enterprise = user.enterprise
    
    conversion_data = calculate_conversion_rates(enterprise)
    
    context = {
        'conversion_data': conversion_data,
    }
    
    return render(request, 'reports/clients/conversion.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def clients_status_analysis_view(request):
    """Análise detalhada por status de cliente"""
    # Implementar análise de status
    pass


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def clients_repurchase_view(request):
    """Análise detalhada de recompra"""
    # Implementar análise de recompra
    pass


# ==================== RELATÓRIOS DE DESEMPENHO ====================

@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def performance_captadores_view(request):
    """Ranking e performance dos captadores"""
    user = request.user
    enterprise = user.enterprise
    
    # Buscar usuários com role de captador
    captadores = User.objects.filter(
        enterprise=enterprise,
        roles__code='captador',
        is_active=True
    ).annotate(
        clients_captured=Count('prospected_projects__client', distinct=True),
        total_value=Sum('prospected_projects__value')
    ).order_by('-clients_captured')
    
    context = {
        'captadores': captadores,
    }
    
    return render(request, 'reports/performance/captadores.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def performance_projetistas_view(request):
    """Ranking e performance dos projetistas"""
    user = request.user
    enterprise = user.enterprise
    
    # Buscar usuários com role de projetista
    projetistas = User.objects.filter(
        enterprise=enterprise,
        roles__code='projetista',
        is_active=True
    ).annotate(
        projects_designed=Count('designed_projects'),
        approved_projects=Count('designed_projects', filter=Q(designed_projects__status__in=['AP', 'AF', 'FM', 'LB', 'RC'])),
        total_value=Sum('designed_projects__value'),
        active_projects=Count('designed_projects', filter=Q(designed_projects__status__in=['AC', 'PE', 'AN']))
    ).order_by('-projects_designed')
    
    context = {
        'projetistas': projetistas,
    }
    
    return render(request, 'reports/performance/projetistas.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def performance_unidades_view(request):
    """Performance das unidades"""
    user = request.user
    enterprise = user.enterprise
    
    unidades = Unit.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).annotate(
        total_projects=Count('projects'),
        approved_projects=Count('projects', filter=Q(projects__status__in=['AP', 'AF', 'FM', 'LB', 'RC'])),
        total_value=Sum('projects__value'),
        active_clients=Count('clients', filter=Q(clients__status='ATIVO'))
    ).order_by('-total_projects')
    
    context = {
        'unidades': unidades,
    }
    
    return render(request, 'reports/performance/unidades.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def performance_bancos_view(request):
    """Performance dos bancos"""
    user = request.user
    enterprise = user.enterprise
    
    bancos = Bank.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).annotate(
        total_projects=Count('projects'),
        approved_projects=Count('projects', filter=Q(projects__status__in=['AP', 'AF', 'FM', 'LB', 'RC'])),
        total_value=Sum('projects__value'),
        avg_ticket=Avg('projects__value')
    ).order_by('-total_projects')
    
    context = {
        'bancos': bancos,
    }
    
    return render(request, 'reports/performance/bancos.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def performance_carteira_view(request):
    """Análise de carteira ativa"""
    # Implementar análise de carteira
    pass


# ==================== RELATÓRIOS POR CATEGORIA ====================

@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def categories_client_size_view(request):
    """Relatório por tamanho de cliente"""
    # Implementar por tamanho
    pass


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def categories_operation_type_view(request):
    """Relatório por tipo de operação (Custeio/Investimento)"""
    # Implementar por tipo
    pass


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def categories_by_unit_view(request):
    """Relatório comparativo por unidade"""
    # Implementar comparativo
    pass


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def categories_comparative_view(request):
    """Relatório comparativo geral"""
    # Implementar comparativo geral
    pass


# ==================== RELATÓRIOS ESPECIAIS ====================

@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def special_vencimentos_view(request):
    """Relatório de vencimentos de operações"""
    # Implementar vencimentos
    pass


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def special_aniversarios_view(request):
    """Relatório de clientes aniversariantes"""
    user = request.user
    enterprise = user.enterprise
    
    today = timezone.now().date()
    
    # Aniversariantes de hoje
    today_birthdays = Client.objects.filter(
        enterprise=enterprise,
        date_of_birth__month=today.month,
        date_of_birth__day=today.day,
        is_active=True
    )
    
    # Aniversariantes desta semana
    week_start = today
    week_end = today + timedelta(days=7)
    
    # Para SQLite, buscar aniversariantes nos próximos 7 dias usando Python
    week_birthdays = []
    for i in range(7):
        current_day = today + timedelta(days=i)
        daily_birthdays = Client.objects.filter(
            enterprise=enterprise,
            date_of_birth__month=current_day.month,
            date_of_birth__day=current_day.day,
            is_active=True
        )
        week_birthdays.extend(daily_birthdays)
    
    # Remover duplicatas (caso um cliente apareça mais de uma vez)
    week_birthdays = list(set(week_birthdays))
    
    context = {
        'today_birthdays': today_birthdays,
        'week_birthdays': week_birthdays,
        'week_birthdays_count': len(week_birthdays),
    }
    
    return render(request, 'reports/special/aniversarios.html', context)


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def special_carteira_contatos_view(request):
    """Relatório da carteira de contatos"""
    # Implementar carteira de contatos
    pass


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def special_franqueados_view(request):
    """Relatório de desempenho por franqueado"""
    # Implementar franqueados
    pass


@login_required
@permission_required('users.view_reports', 'Você não tem permissão para visualizar relatórios.')
def special_comissoes_view(request):
    """Relatório de comissões e royalties"""
    # Implementar comissões
    pass


# ==================== CONFIGURAÇÕES ====================

@login_required
def reports_settings_view(request):
    """Configurações do sistema de relatórios"""
    user = request.user
    
    # Buscar ou criar configurações do usuário
    settings, created = ReportSettings.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Atualizar configurações
        settings.default_period_days = int(request.POST.get('default_period_days', 365))
        settings.auto_refresh_enabled = request.POST.get('auto_refresh_enabled') == 'on'
        settings.auto_refresh_interval = int(request.POST.get('auto_refresh_interval', 60))
        settings.email_reports_enabled = request.POST.get('email_reports_enabled') == 'on'
        settings.email_frequency = request.POST.get('email_frequency', 'weekly')
        
        # Metas
        settings.target_proposals_month = request.POST.get('target_proposals_month') or None
        settings.target_approval_time_days = request.POST.get('target_approval_time_days') or None
        settings.target_conversion_rate = request.POST.get('target_conversion_rate') or None
        settings.target_repurchase_rate = request.POST.get('target_repurchase_rate') or None
        
        settings.save()
        messages.success(request, 'Configurações salvas com sucesso!')
        return redirect('reports_settings')
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'reports/settings.html', context)


@login_required
@permission_required('users.export_reports', 'Você não tem permissão para exportar relatórios.')
def reports_export_view(request):
    """Exportação de relatórios"""
    if request.method == 'POST':
        export_type = request.POST.get('export_type')  # 'excel' ou 'pdf'
        report_type = request.POST.get('report_type')
        
        if export_type == 'excel':
            return export_to_excel(request.user.enterprise, report_type)
        elif export_type == 'pdf':
            return export_to_pdf(request.user.enterprise, report_type)
    
    return render(request, 'reports/export.html')


# ==================== APIs PARA AJAX ====================

@login_required
def api_dashboard_data_view(request):
    """API para dados do dashboard"""
    # Retornar dados em JSON para gráficos
    return JsonResponse({'status': 'success', 'data': {}})


@login_required
def api_operations_chart_view(request):
    """API para gráficos de operações"""
    # Retornar dados para gráficos
    return JsonResponse({'status': 'success', 'data': {}})


@login_required
def api_clients_chart_view(request):
    """API para gráficos de clientes"""
    # Retornar dados para gráficos
    return JsonResponse({'status': 'success', 'data': {}})


@login_required
def api_performance_chart_view(request):
    """API para gráficos de performance"""
    # Retornar dados para gráficos
    return JsonResponse({'status': 'success', 'data': {}})


@login_required
def api_refresh_cache_view(request):
    """API para limpar cache de relatórios"""
    if request.method == 'POST':
        ReportCache.objects.filter(enterprise=request.user.enterprise).delete()
        return JsonResponse({'status': 'success', 'message': 'Cache limpo com sucesso'})
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})
