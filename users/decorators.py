from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

def permission_required(permission, message=None, redirect_url='home'):
    """
    Decorator que verifica se o usuário tem uma permissão específica
    
    Args:
        permission (str): Permissão no formato 'app.codename' (ex: 'usuarios.add_usuarios')
        message (str): Mensagem de erro personalizada
        redirect_url (str): URL para redirecionamento em caso de erro
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                error_message = message or f'Você não tem permissão para esta ação.'
                messages.error(request, error_message)
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def module_permission_required(module, action, message=None, redirect_url='home'):
    """
    Decorator que verifica permissão por módulo e ação
    
    Args:
        module (str): Código do módulo (ex: 'usuarios', 'projetos')
        action (str): Ação (ex: 'view', 'add', 'change', 'delete')
        message (str): Mensagem de erro personalizada
        redirect_url (str): URL para redirecionamento
    """
    permission = f'users.{action}_{module}'
    return permission_required(permission, message, redirect_url)

def role_required(role_codes, message=None, redirect_url='home'):
    """
    Decorator que verifica se o usuário tem um dos cargos especificados
    
    Args:
        role_codes (list): Lista de códigos de cargos (ex: ['ceo', 'diretor'])
        message (str): Mensagem de erro personalizada
        redirect_url (str): URL para redirecionamento
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user_role_codes = list(request.user.roles.filter(is_active=True).values_list('code', flat=True))
            
            if not any(role in role_codes for role in user_role_codes):
                error_message = message or 'Seu cargo não tem acesso a esta funcionalidade.'
                messages.error(request, error_message)
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def reports_permission_required(message=None, redirect_url='home'):
    """
    Decorator que verifica permissão de visualizar relatórios
    e automaticamente filtra dados por unidades acessíveis
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Verificar permissão de relatórios
            if not request.user.has_perm('users.view_reports'):
                error_message = message or 'Você não tem permissão para visualizar relatórios.'
                messages.error(request, error_message)
                return redirect(redirect_url)
            
            # Adicionar unidades acessíveis ao request para uso na view
            from reports.utils import get_user_accessible_units
            request.accessible_units = get_user_accessible_units(request.user)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def any_permission_required(permissions, message=None, redirect_url='home'):
    """
    Decorator que verifica se o usuário tem pelo menos uma das permissões especificadas
    
    Args:
        permissions (list): Lista de permissões (ex: ['usuarios.view_usuarios', 'usuarios.add_usuarios'])
        message (str): Mensagem de erro personalizada
        redirect_url (str): URL para redirecionamento
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not any(request.user.has_perm(perm) for perm in permissions):
                error_message = message or 'Você não tem as permissões necessárias para esta ação.'
                messages.error(request, error_message)
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def all_permissions_required(permissions, message=None, redirect_url='home'):
    """
    Decorator que verifica se o usuário tem todas as permissões especificadas
    
    Args:
        permissions (list): Lista de permissões (ex: ['usuarios.view_usuarios', 'usuarios.add_usuarios'])
        message (str): Mensagem de erro personalizada
        redirect_url (str): URL para redirecionamento
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not all(request.user.has_perm(perm) for perm in permissions):
                error_message = message or 'Você não tem todas as permissões necessárias para esta ação.'
                messages.error(request, error_message)
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def ajax_permission_required(permission):
    """
    Decorator para views AJAX que retorna status 403 em caso de falta de permissão
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                return HttpResponseForbidden('Permissão negada')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 