from django import template
from django.contrib.auth.models import Permission

register = template.Library()

@register.filter
def has_perm(user, permission):
    """
    Verifica se o usuário tem uma permissão específica
    Uso: {% if user|has_perm:"users.add_users" %}
    """
    if not user or not user.is_authenticated:
        return False
    return user.has_perm(permission)

@register.filter
def has_any_perm(user, permissions):
    """
    Verifica se o usuário tem pelo menos uma das permissões
    Uso: {% if user|has_any_perm:"users.add_users,users.change_usuarios" %}
    """
    if not user or not user.is_authenticated:
        return False
    perm_list = permissions.split(',')
    return any(user.has_perm(perm.strip()) for perm in perm_list)

@register.filter
def has_all_perms(user, permissions):
    """
    Verifica se o usuário tem todas as permissões
    Uso: {% if user|has_all_perms:"users.add_users,users.change_usuarios" %}
    """
    if not user or not user.is_authenticated:
        return False
    perm_list = permissions.split(',')
    return all(user.has_perm(perm.strip()) for perm in perm_list)

@register.filter
def has_role(user, role_code):
    """
    Verifica se o usuário tem um cargo específico
    Uso: {% if user|has_role:"ceo" %}
    """
    if not user or not user.is_authenticated:
        return False
    return user.roles.filter(code=role_code, is_active=True).exists()

@register.filter
def has_any_role(user, role_codes):
    """
    Verifica se o usuário tem pelo menos um dos cargos
    Uso: {% if user|has_any_role:"ceo,diretor" %}
    """
    if not user or not user.is_authenticated:
        return False
    codes = role_codes.split(',')
    return user.roles.filter(code__in=[code.strip() for code in codes], is_active=True).exists()

@register.simple_tag
def user_permissions(user):
    """
    Retorna todas as permissões do usuário
    Uso: {% user_permissions user as perms %}
    """
    if not user or not user.is_authenticated:
        return []
    return user.get_all_permissions()

@register.simple_tag
def user_roles(user):
    """
    Retorna todos os cargos do usuário
    Uso: {% user_roles user as roles %}
    """
    if not user or not user.is_authenticated:
        return []
    return user.roles.filter(is_active=True)

@register.inclusion_tag('users/partials/permission_debug.html')
def debug_permissions(user):
    """
    Tag para debugar permissões (usar apenas em desenvolvimento)
    Uso: {% debug_permissions user %}
    """
    if not user or not user.is_authenticated:
        return {'user': None}
    
    return {
        'user': user,
        'all_permissions': user.get_all_permissions(),
        'roles': user.roles.filter(is_active=True),
        'custom_permissions': user.custom_permissions.all(),
    } 