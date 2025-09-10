def user_units_context(request):
    """Context processor para disponibilizar unidades do usuário"""
    context = {
        'user_units': [],
        'all_enterprise_units': [],
        'selected_unit': None,
        'has_multiple_units': False,
        'can_view_all_units': False,
        'is_all_units_selected': False
    }
    
    if request.user.is_authenticated:
        # Verificar se o usuário pode ver todas as unidades
        can_view_all_units = request.user.has_perm('users.view_all_units')
        context['can_view_all_units'] = can_view_all_units
        
        if can_view_all_units:
            # Usuário com permissão total: pode ver todas as unidades da empresa
            all_units = request.user.enterprise.units.filter(is_active=True).order_by('name')
            context['user_units'] = all_units  # Para compatibilidade
            context['all_enterprise_units'] = all_units
            context['has_multiple_units'] = True  # Sempre mostrar seletor
            
            # Para usuários com view_all_units, padrão é "Todas as unidades"
            selected_unit_id = request.session.get('selected_unit_id')
            if not selected_unit_id:
                # Definir "Todas as unidades" como padrão
                request.session['selected_unit_id'] = 'all'
                context['is_all_units_selected'] = True
                context['selected_unit'] = None
            elif selected_unit_id == 'all':
                context['is_all_units_selected'] = True
                context['selected_unit'] = None
            else:
                try:
                    # Pode selecionar qualquer unidade da empresa
                    selected_unit = all_units.get(id=selected_unit_id)
                    context['selected_unit'] = selected_unit
                except:
                    # Se unidade não existe, voltar para "Todas as unidades"
                    request.session['selected_unit_id'] = 'all'
                    context['is_all_units_selected'] = True
                    context['selected_unit'] = None
        else:
            # Usuário normal: apenas suas unidades vinculadas
            user_units = request.user.units.filter(is_active=True).order_by('name')
            context['user_units'] = user_units
            context['has_multiple_units'] = user_units.count() > 1
            
            # Buscar unidade selecionada na sessão
            selected_unit_id = request.session.get('selected_unit_id')
            if selected_unit_id and selected_unit_id != 'all':
                try:
                    selected_unit = user_units.get(id=selected_unit_id)
                    context['selected_unit'] = selected_unit
                except:
                    # Se a unidade não existe mais ou usuário perdeu acesso, limpar sessão
                    if 'selected_unit_id' in request.session:
                        del request.session['selected_unit_id']
            
            # Se não tem unidade selecionada mas tem unidades, selecionar a primeira
            if not context['selected_unit'] and user_units.exists():
                first_unit = user_units.first()
                context['selected_unit'] = first_unit
                request.session['selected_unit_id'] = first_unit.id
    
    return context 