from datetime import date
from django.utils import timezone
from django.dispatch import receiver
from .middleware import get_current_user
from django.contrib.auth import get_user_model
from .models import Project, ProjectHistory, ProjectDocument
from django.db.models.signals import pre_save, post_save, post_delete
from .models import PROJECT_STATUS_CHOICES, ACTIVITY_CHOICES, SIZE_CHOICES
PROJECT_STATUS_MAP = dict(PROJECT_STATUS_CHOICES)
ACTIVITY_MAP = dict(ACTIVITY_CHOICES)
SIZE_MAP = dict(SIZE_CHOICES)

User = get_user_model()

def format_value(value, field_name):
    if value is None:
        return 'Não definido'
    
    if isinstance(value, date) or field_name in ['next_phase_deadline', 'first_installment_date', 'last_installment_date', 'approval_date', 'start_date', 'end_date']:
        if isinstance(value, str):
            try:
                if '-' in value:
                    year, month, day = value.split('-')
                    return f"{day}/{month}/{year}"
                return value
            except:
                return value
        return value.strftime('%d/%m/%Y')
    
    if field_name == 'status':
        return PROJECT_STATUS_MAP.get(str(value), value)
    elif field_name == 'activity':
        return ACTIVITY_MAP.get(str(value), value)
    elif field_name == 'size':
        return SIZE_MAP.get(str(value), value)
    elif field_name == 'project_finalized':
        return 'Sim' if value else 'Não'
    
    if hasattr(value, 'pk'):
        return str(value)
    
    if isinstance(value, float) or isinstance(value, int):
        if any(field_name.endswith(suffix) for suffix in ['_value', 'value', 'fees', 'percentage_astec']) or field_name in ['received_value', 'consortium_value']:
            return f"{value:,.2f}"
    
    return str(value)

def get_user_display_name(user):
    if user is None:
        return "Sistema"
    
    try:
        if hasattr(user, 'get_full_name'):
            full_name = user.get_full_name().strip()
            if full_name:
                return full_name
        
        if hasattr(user, 'name'):
            if user.name:
                return user.name
        
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            if user.first_name or user.last_name:
                return f"{user.first_name} {user.last_name}".strip()
                
        if hasattr(user, 'username'):
            return user.username
            
        return str(user)
    except Exception:
        return "Sistema"

def format_file_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

@receiver(pre_save, sender=Project)
def track_project_changes(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous = Project.objects.get(pk=instance.pk)
        changes = {}
        current_user = get_current_user()
        user_name = get_user_display_name(current_user)
        
        tracked_fields = {
            'description': 'Descrição',
            'start_date': 'Data de Início',
            'end_date': 'Data de Término',
            'status': 'Status',
            'credit_line': 'Linha de Crédito',
            'bank': 'Banco',
            'value': 'Valor do Projeto',
            'land_size': 'Tamanho da Terra',
            'activity': 'Atividade',
            'size': 'Tamanho do Projeto',
            'documents_description': 'Descrição de Documentos',
            'project_deadline': 'Prazo do Projeto',
            'installments': 'Parcelas',
            'percentage_astec': 'Porcentagem ASTEC',
            'next_phase_deadline': 'Prazo Próxima Fase',
            'project_manager': 'Gerente do Projeto',
            'project_designer': 'Projetista',
            'client': 'Cliente',
            'enterprise': 'Empresa',
            'unit': 'Unidade',
            'fees': 'Juros',
            'payment_grace': 'Carência',
            'approval_date': 'Data de Aprovação',
            'consortium_value': 'Valor do Consórcio',
            'first_installment_date': 'Data Primeira Parcela',
            'last_installment_date': 'Data Última Parcela',
            'received_value': 'Valor Recebido',
            'project_finalized': 'Projeto Finalizado',
            'project_prospector': 'Prospector'
        }

        for field, field_name in tracked_fields.items():
            old_value = getattr(previous, field)
            new_value = getattr(instance, field)

            if old_value != new_value:
                changes[field] = {
                    'usuario': user_name,
                    'campo': field_name,
                    'de': format_value(old_value, field),
                    'para': format_value(new_value, field),
                    'data': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
                }

        if changes:
            ProjectHistory.objects.create(
                project=instance,
                changes=changes,
            )

    except Project.DoesNotExist:
        pass

@receiver(post_save, sender=ProjectDocument)
def track_document_addition(sender, instance, created, **kwargs):
    if created:
        current_user = get_current_user()
        user_name = get_user_display_name(current_user)
        
        changes = {
            'document_added': {
                'usuario': user_name,
                'campo': 'Documento',
                'acao': 'Adicionou',
                'arquivo': instance.file_name,
                'tipo': instance.file_type,
                'tamanho': format_file_size(instance.file_size),
                'data': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
            }
        }
        
        ProjectHistory.objects.create(
            project=instance.project,
            changes=changes,
        )

@receiver(post_delete, sender=ProjectDocument)
def track_document_deletion(sender, instance, **kwargs):
    current_user = get_current_user()
    user_name = get_user_display_name(current_user)
    
    changes = {
        'document_deleted': {
            'usuario': user_name,
            'campo': 'Documento',
            'acao': 'Removeu',
            'arquivo': instance.file_name,
            'tipo': instance.file_type,
            'tamanho': format_file_size(instance.file_size),
            'data': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
        }
    }
    
    ProjectHistory.objects.create(
        project=instance.project,
        changes=changes,
    )