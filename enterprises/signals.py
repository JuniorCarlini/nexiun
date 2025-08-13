from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Client, ClientDocument, ClientHistory
from projects.signals import get_current_user, get_user_display_name


def format_value(value, field):
    """Formata valores para exibição no histórico"""
    if value is None:
        return "Não informado"
    
    # Formatação específica para campos de data
    if field in ['date_of_birth', 'retorno_ate', 'created_at', 'updated_at']:
        if hasattr(value, 'strftime'):
            return value.strftime('%d/%m/%Y')
        return str(value)
    
    # Formatação para campos de relacionamento
    if field in ['created_by', 'enterprise']:
        return str(value) if value else "Não informado"
    
    # Formatação para status
    if field == 'status':
        status_dict = {
            'INATIVO': 'Inativo',
            'INTERESSADO': 'Interessado',
            'EM_NEGOCIACAO': 'Em Negociação',
            'ATIVO': 'Ativo'
        }
        return status_dict.get(value, str(value))
    
    # Formatação para campos booleanos
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    
    return str(value)


def format_file_size(size_in_bytes):
    """Formata o tamanho do arquivo para exibição"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"


@receiver(pre_save, sender=Client)
def track_client_changes(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous = Client.objects.get(pk=instance.pk)
        changes = {}
        current_user = get_current_user()
        user_name = get_user_display_name(current_user)
        
        tracked_fields = {
            'name': 'Nome',
            'email': 'Email',
            'phone': 'Telefone',
            'address': 'Endereço',
            'city': 'Cidade',
            'observations': 'Observações',
            'date_of_birth': 'Data de Aniversário',
            'status': 'Status',
            'retorno_ate': 'Retorno até',
            'enterprise': 'Empresa',
            'created_by': 'Cadastrado por',
            'is_active': 'Ativo',
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

        # Verificar mudanças nas unidades (Many-to-Many)
        if hasattr(previous, '_state') and not previous._state.adding:
            old_units = set(previous.units.all())
            # Não podemos acessar as novas unidades aqui no pre_save
            # Isso será tratado em um signal post_save

        if changes:
            ClientHistory.objects.create(
                client=instance,
                changes=changes,
            )

    except Client.DoesNotExist:
        pass


@receiver(post_save, sender=Client)
def track_client_units_changes(sender, instance, **kwargs):
    """Rastreia mudanças nas unidades do cliente (Many-to-Many)"""
    # Só verifica se o cliente já existia (não é novo)
    if not kwargs.get('created', False):
        try:
            # Buscar o histórico mais recente para adicionar mudanças de unidades se necessário
            current_user = get_current_user()
            user_name = get_user_display_name(current_user)
            
            # Este signal será usado principalmente para mudanças futuras nas unidades
            # por enquanto, apenas criamos um registro se houver necessidade específica
            pass
            
        except Exception as e:
            pass


@receiver(post_save, sender=ClientDocument)
def track_client_document_addition(sender, instance, created, **kwargs):
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
        
        ClientHistory.objects.create(
            client=instance.client,
            changes=changes,
        )


@receiver(post_delete, sender=ClientDocument)
def track_client_document_deletion(sender, instance, **kwargs):
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
    
    ClientHistory.objects.create(
        client=instance.client,
        changes=changes,
    ) 