from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


class UnitFilterMixin(LoginRequiredMixin):
    """
    Mixin para filtrar dados pela unidade selecionada na sessão
    """
    
    def get_selected_unit(self):
        """Retorna a unidade selecionada na sessão"""
        if not self.request.user.is_authenticated:
            return None
            
        selected_unit_id = self.request.session.get('selected_unit_id')
        
        # Se selecionou "Todas as unidades", retorna None (indicando todas)
        if selected_unit_id == 'all' and self.request.user.has_perm('users.view_all_units'):
            return None
            
        if selected_unit_id:
            try:
                # Se tem permissão para ver todas as unidades, pode acessar qualquer unidade da empresa
                if self.request.user.has_perm('users.view_all_units'):
                    return self.request.user.enterprise.units.filter(
                        id=selected_unit_id, 
                        is_active=True
                    ).first()
                else:
                    # Usuário normal: só suas unidades vinculadas
                    return self.request.user.units.filter(
                        id=selected_unit_id, 
                        is_active=True
                    ).first()
            except:
                return None
        
        # Se não tem unidade selecionada
        if self.request.user.has_perm('users.view_all_units'):
            # Para usuários com view_all_units, padrão é "Todas as unidades"
            return None
        else:
            # Para usuários normais, retorna a primeira unidade vinculada
            return self.request.user.units.filter(is_active=True).first()
    
    def is_all_units_selected(self):
        """Verifica se está selecionado 'Todas as unidades'"""
        selected_unit_id = self.request.session.get('selected_unit_id')
        return (selected_unit_id == 'all' and 
                self.request.user.has_perm('users.view_all_units'))
    
    def get_accessible_units(self):
        """Retorna todas as unidades que o usuário pode acessar"""
        if self.request.user.has_perm('users.view_all_units'):
            # Pode acessar todas as unidades da empresa
            return self.request.user.enterprise.units.filter(is_active=True)
        else:
            # Só pode acessar suas unidades vinculadas
            return self.request.user.units.filter(is_active=True)
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica se usuário tem acesso a unidades"""
        if request.user.is_authenticated:
            # Usuários com view_all_units não precisam estar vinculados a unidades específicas
            if not request.user.has_perm('users.view_all_units'):
                if not request.user.units.filter(is_active=True).exists():
                    messages.warning(
                        request, 
                        'Você não tem acesso a nenhuma unidade. Entre em contato com o administrador.'
                    )
                    return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Adiciona a unidade selecionada no contexto"""
        context = super().get_context_data(**kwargs)
        context['current_unit'] = self.get_selected_unit()
        context['is_all_units_selected'] = self.is_all_units_selected()
        return context


def unit_filter_required(view_func):
    """
    Decorator para views baseadas em função que precisam de unidade selecionada
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Usuários com view_all_units não precisam estar vinculados a unidades específicas
        if not request.user.has_perm('users.view_all_units'):
            # Verificar se usuário tem unidades
            if not request.user.units.filter(is_active=True).exists():
                messages.warning(
                    request, 
                    'Você não tem acesso a nenhuma unidade. Entre em contato com o administrador.'
                )
                return redirect('home')
        
        # Garantir que há uma unidade selecionada
        selected_unit_id = request.session.get('selected_unit_id')
        if not selected_unit_id:
            if request.user.has_perm('users.view_all_units'):
                # Para usuários com view_all_units, padrão é "Todas as unidades"
                request.session['selected_unit_id'] = 'all'
            else:
                # Para usuários normais, selecionar primeira unidade vinculada
                first_unit = request.user.units.filter(is_active=True).first()
                if first_unit:
                    request.session['selected_unit_id'] = first_unit.id
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_selected_unit_from_request(request):
    """
    Função helper para obter a unidade selecionada de uma request
    """
    if not request.user.is_authenticated:
        return None
        
    selected_unit_id = request.session.get('selected_unit_id')
    
    # Se selecionou "Todas as unidades", retorna None (indicando todas)
    if selected_unit_id == 'all' and request.user.has_perm('users.view_all_units'):
        return None
        
    if selected_unit_id:
        try:
            # Se tem permissão para ver todas as unidades, pode acessar qualquer unidade da empresa
            if request.user.has_perm('users.view_all_units'):
                return request.user.enterprise.units.filter(
                    id=selected_unit_id, 
                    is_active=True
                ).first()
            else:
                # Usuário normal: só suas unidades vinculadas
                return request.user.units.filter(
                    id=selected_unit_id, 
                    is_active=True
                ).first()
        except:
            return None
    
    # Se não tem unidade selecionada
    if request.user.has_perm('users.view_all_units'):
        # Para usuários com view_all_units, padrão é "Todas as unidades"
        return None
    else:
        # Para usuários normais, retorna a primeira unidade vinculada
        return request.user.units.filter(is_active=True).first()


def is_all_units_selected_from_request(request):
    """
    Função helper para verificar se está selecionado 'Todas as unidades'
    """
    selected_unit_id = request.session.get('selected_unit_id')
    return (selected_unit_id == 'all' and 
            request.user.has_perm('users.view_all_units'))


def get_accessible_units_from_request(request):
    """
    Função helper para obter todas as unidades que o usuário pode acessar
    """
    if not request.user.is_authenticated:
        return []
    
    if request.user.has_perm('users.view_all_units'):
        # Pode acessar todas as unidades da empresa
        return request.user.enterprise.units.filter(is_active=True)
    else:
        # Só pode acessar suas unidades vinculadas
        return request.user.units.filter(is_active=True) 