from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

class PermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin que verifica se o usuário tem uma permissão específica
    """
    permission_required = None
    permission_denied_message = 'Você não tem permissão para esta ação.'
    redirect_url = 'home'

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        if self.permission_required is None:
            raise AttributeError(
                'PermissionRequiredMixin requires permission_required to be set'
            )
        return self.request.user.has_perm(self.permission_required)

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)

class ModulePermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin que verifica permissão por módulo e ação
    """
    module_code = None
    action = None
    permission_denied_message = 'Você não tem permissão para esta ação.'
    redirect_url = 'home'

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        if self.module_code is None or self.action is None:
            raise AttributeError(
                'ModulePermissionRequiredMixin requires module_code and action to be set'
            )
        permission = f'users.{self.action}_{self.module_code}'
        return self.request.user.has_perm(permission)

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)

class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin que verifica se o usuário tem um dos cargos especificados
    """
    role_codes = None
    permission_denied_message = 'Seu cargo não tem acesso a esta funcionalidade.'
    redirect_url = 'home'

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        if self.role_codes is None:
            raise AttributeError(
                'RoleRequiredMixin requires role_codes to be set'
            )
        user_role_codes = list(
            self.request.user.roles.filter(is_active=True).values_list('code', flat=True)
        )
        return any(role in self.role_codes for role in user_role_codes)

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)

class MultiplePermissionsRequiredMixin(LoginRequiredMixin):
    """
    Mixin que verifica múltiplas permissões
    """
    permissions_required = None
    require_all_permissions = True  # Se False, verifica se tem pelo menos uma
    permission_denied_message = 'Você não tem as permissões necessárias para esta ação.'
    redirect_url = 'home'

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        if self.permissions_required is None:
            raise AttributeError(
                'MultiplePermissionsRequiredMixin requires permissions_required to be set'
            )
        
        if self.require_all_permissions:
            return all(self.request.user.has_perm(perm) for perm in self.permissions_required)
        else:
            return any(self.request.user.has_perm(perm) for perm in self.permissions_required)

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)

class AjaxPermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin para views AJAX que retorna status 403 em caso de falta de permissão
    """
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return HttpResponseForbidden('Permissão negada')
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        if self.permission_required is None:
            raise AttributeError(
                'AjaxPermissionRequiredMixin requires permission_required to be set'
            )
        return self.request.user.has_perm(self.permission_required) 