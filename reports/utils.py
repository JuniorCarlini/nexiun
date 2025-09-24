from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
import hashlib
import json
from io import BytesIO

from projects.models import Project, ProjectHistory
from enterprises.models import Client
from units.models import Unit


def calculate_approval_time(enterprise, start_date=None, detailed=False):
    """
    Calcula tempo médio de aprovação com base no histórico de mudanças
    """
    if start_date is None:
        start_date = timezone.now().date() - timedelta(days=365)
    
    # Buscar projetos aprovados no período
    approved_projects = Project.objects.filter(
        enterprise=enterprise,
        status__in=['AP', 'AF', 'FM', 'LB', 'RC'],
        approval_date__isnull=False,
        created_at__date__gte=start_date
    )
    
    if not detailed:
        # Retorno simples: média geral
        total_days = 0
        count = 0
        
        for project in approved_projects:
            if project.approval_date and project.created_at:
                days = (project.approval_date - project.created_at.date()).days
                if days >= 0:  # Validação básica
                    total_days += days
                    count += 1
        
        return round(total_days / count, 1) if count > 0 else 0
    
    # Retorno detalhado: por fase, banco, unidade, etc.
    detailed_data = {
        'overall_average': 0,
        'by_bank': {},
        'by_unit': {},
        'by_project_type': {},
        'phase_breakdown': {}
    }
    
    # Implementar cálculo detalhado aqui
    # ...
    
    return detailed_data


def calculate_conversion_rates(enterprise):
    """
    Calcula taxas de conversão do funil de vendas
    """
    # Total de clientes por status
    clients_by_status = Client.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).values('status').annotate(count=Count('id'))
    
    # Converter para dict
    status_counts = {item['status']: item['count'] for item in clients_by_status}
    
    # Calcular conversões
    total_contacts = sum(status_counts.values())
    interested = status_counts.get('INTERESSADO', 0)
    negotiating = status_counts.get('EM_NEGOCIACAO', 0)
    active = status_counts.get('ATIVO', 0)
    
    # Projetos criados vs clientes ativos
    projects_created = Project.objects.filter(
        enterprise=enterprise,
        is_active=True
    ).count()
    
    projects_approved = Project.objects.filter(
        enterprise=enterprise,
        status__in=['AP', 'AF', 'FM', 'LB', 'RC'],
        is_active=True
    ).count()
    
    conversion_data = {
        'total_contacts': total_contacts,
        'interested': interested,
        'negotiating': negotiating,
        'active_clients': active,
        'projects_created': projects_created,
        'projects_approved': projects_approved,
        'rates': {
            'contact_to_interested': (interested / total_contacts * 100) if total_contacts > 0 else 0,
            'interested_to_negotiating': (negotiating / interested * 100) if interested > 0 else 0,
            'negotiating_to_active': (active / negotiating * 100) if negotiating > 0 else 0,
            'active_to_project': (projects_created / active * 100) if active > 0 else 0,
            'project_to_approved': (projects_approved / projects_created * 100) if projects_created > 0 else 0,
        }
    }
    
    return conversion_data


def generate_performance_metrics(enterprise, group_by='unit'):
    """
    Gera métricas de performance agrupadas por critério
    """
    if group_by == 'bank':
        return Project.objects.filter(
            enterprise=enterprise,
            is_active=True
        ).values(
            'bank__name'
        ).annotate(
            total_projects=Count('id'),
            approved_projects=Count('id', filter=Q(status__in=['AP', 'AF', 'FM', 'LB', 'RC'])),
            total_value=Sum('value'),
            avg_value=Avg('value')
        ).order_by('-total_projects')
    
    elif group_by == 'credit_line':
        return Project.objects.filter(
            enterprise=enterprise,
            is_active=True
        ).values(
            'credit_line__name',
            'credit_line__type_credit'
        ).annotate(
            total_projects=Count('id'),
            approved_projects=Count('id', filter=Q(status__in=['AP', 'AF', 'FM', 'LB', 'RC'])),
            total_value=Sum('value'),
            avg_value=Avg('value')
        ).order_by('-total_projects')
    
    elif group_by == 'unit':
        return Project.objects.filter(
            enterprise=enterprise,
            is_active=True
        ).values(
            'unit__name'
        ).annotate(
            total_projects=Count('id'),
            approved_projects=Count('id', filter=Q(status__in=['AP', 'AF', 'FM', 'LB', 'RC'])),
            total_value=Sum('value'),
            avg_value=Avg('value')
        ).order_by('-total_projects')
    
    return []


def generate_cache_key(report_type, filters):
    """
    Gera chave única para cache baseada no tipo de relatório e filtros
    """
    filter_str = json.dumps(filters, sort_keys=True)
    return hashlib.sha256(f"{report_type}_{filter_str}".encode()).hexdigest()


def export_to_excel(enterprise, report_type):
    """
    Exporta relatório para Excel
    """
    try:
        import xlsxwriter
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Relatório')
        
        # Configurar cabeçalhos e dados baseado no report_type
        if report_type == 'operations_performance':
            headers = ['Projeto', 'Cliente', 'Status', 'Banco', 'Valor', 'Data Criação']
            projects = Project.objects.filter(enterprise=enterprise, is_active=True)
            
            # Escrever cabeçalhos
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)
            
            # Escrever dados
            for row, project in enumerate(projects, 1):
                worksheet.write(row, 0, str(project))
                worksheet.write(row, 1, project.client.name)
                worksheet.write(row, 2, project.get_status_display())
                worksheet.write(row, 3, project.bank.name)
                worksheet.write(row, 4, float(project.value or 0))
                worksheet.write(row, 5, project.created_at.strftime('%d/%m/%Y'))
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="relatorio_{report_type}.xlsx"'
        
        return response
    
    except ImportError:
        # Se xlsxwriter não estiver instalado, retornar CSV simples
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="relatorio_{report_type}.csv"'
        response.write('Funcionalidade de Excel requer xlsxwriter instalado')
        return response


def export_to_pdf(enterprise, report_type):
    """
    Exporta relatório para PDF
    """
    try:
        import reportlab
        # Implementar exportação para PDF usando reportlab
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_{report_type}.pdf"'
        
        # TODO: Implementar geração do PDF
        response.write(b'PDF em desenvolvimento')
        
        return response
    
    except ImportError:
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="relatorio_{report_type}.txt"'
        response.write('Funcionalidade de PDF requer reportlab instalado')
        return response


def calculate_repurchase_rate(enterprise, group_by=None):
    """
    Calcula taxa de recompra (RPR) geral ou agrupada
    """
    base_query = Client.objects.filter(
        enterprise=enterprise,
        status='ATIVO',
        is_active=True
    )
    
    if group_by == 'unit':
        return base_query.values('units__name').annotate(
            total_clients=Count('id')
        )
    elif group_by == 'captador':
        return base_query.values('created_by__name').annotate(
            total_clients=Count('id')
        )
    
    # Taxa geral
    total_clients = base_query.count()
    repurchase_clients = base_query.annotate(
        project_count=Count('projects')
    ).filter(project_count__gt=1).count()
    
    return (repurchase_clients / total_clients * 100) if total_clients > 0 else 0


def get_upcoming_deadlines(enterprise, days_ahead=30):
    """
    Retorna operações com vencimento próximo
    """
    # Esta função precisará ser implementada quando houver
    # modelo para controle de vencimentos das operações
    return []


def calculate_royalties_by_unit(enterprise, period_start=None, period_end=None):
    """
    Calcula royalties por unidade baseado nas transações
    """
    from units.models import Transaction, Unit
    
    if not period_start:
        period_start = timezone.now().date() - timedelta(days=365)
    if not period_end:
        period_end = timezone.now().date()
    
    royalties_data = []
    
    units = Unit.objects.filter(enterprise=enterprise, is_active=True)
    
    for unit in units:
        # Receitas de crédito rural no período
        receitas = Transaction.objects.filter(
            unit=unit,
            category='RECEITA_CREDITO_RURAL',
            transaction_type='ENTRADA',
            date__range=[period_start, period_end],
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calcular royalties
        royalties_value = receitas * (unit.royalties_percentage / 100)
        marketing_value = receitas * (unit.marketing_percentage / 100)
        
        royalties_data.append({
            'unit': unit,
            'receitas': receitas,
            'royalties_percentage': unit.royalties_percentage,
            'marketing_percentage': unit.marketing_percentage,
            'royalties_value': royalties_value,
            'marketing_value': marketing_value,
            'total_due': royalties_value + marketing_value
        })
    
    return royalties_data


def get_user_accessible_units(user):
    """
    Retorna as unidades que o usuário pode acessar nos relatórios
    baseado em seu cargo e permissões
    
    Cargos com acesso limitado às suas unidades:
    - socio_unidade, franqueado, gerente
    
    Cargos com acesso total:
    - ceo, diretor, coordenador, financeiro
    """
    if not user or not user.is_authenticated:
        return Unit.objects.none()
    
    # Obter códigos dos cargos do usuário
    user_role_codes = list(user.roles.filter(is_active=True).values_list('code', flat=True))
    
    # Cargos com acesso restrito às suas próprias unidades
    restricted_roles = ['socio_unidade', 'franqueado', 'gerente', 'projetista', 'captador']
    
    # Cargos com acesso total
    unrestricted_roles = ['ceo', 'diretor', 'coordenador', 'financeiro']
    
    # Verificar se o usuário tem algum cargo com acesso total
    has_unrestricted_access = any(role in unrestricted_roles for role in user_role_codes)
    
    if has_unrestricted_access:
        # Acesso a todas as unidades da empresa
        return Unit.objects.filter(enterprise=user.enterprise, is_active=True)
    else:
        # Acesso apenas às unidades onde o usuário está vinculado
        return user.units.filter(is_active=True)


def filter_queryset_by_user_units(queryset, user, unit_field='unit'):
    """
    Filtra um queryset baseado nas unidades acessíveis ao usuário
    
    Args:
        queryset: QuerySet a ser filtrado
        user: Usuário logado
        unit_field: Nome do campo que relaciona com Unit (ex: 'unit', 'units', 'client__units')
    
    Returns:
        QuerySet filtrado pelas unidades acessíveis
    """
    accessible_units = get_user_accessible_units(user)
    
    if not accessible_units.exists():
        # Se o usuário não tem acesso a nenhuma unidade, retorna queryset vazio
        return queryset.none()
    
    # Construir filtro baseado no campo fornecido
    if '__' in unit_field:
        # Campo com relacionamento (ex: 'client__units')
        filter_kwargs = {f"{unit_field}__in": accessible_units}
    else:
        # Campo direto (ex: 'unit')
        filter_kwargs = {f"{unit_field}__in": accessible_units}
    
    return queryset.filter(**filter_kwargs)


def get_user_accessible_projects(user, base_queryset=None):
    """
    Retorna projetos acessíveis ao usuário baseado em suas unidades
    """
    if base_queryset is None:
        base_queryset = Project.objects.filter(enterprise=user.enterprise, is_active=True)
    
    return filter_queryset_by_user_units(base_queryset, user, 'unit')


def get_user_accessible_clients(user, base_queryset=None):
    """
    Retorna clientes acessíveis ao usuário baseado em suas unidades
    """
    if base_queryset is None:
        base_queryset = Client.objects.filter(enterprise=user.enterprise, is_active=True)
    
    return filter_queryset_by_user_units(base_queryset, user, 'units') 