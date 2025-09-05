def get_allowed_roles_for_user(user):
    """
    Retorna os códigos dos cargos que o usuário pode atribuir ao criar novos usuários
    baseado na hierarquia definida.
    
    Hierarquia de criação:
    - CEO: Pode criar todos os cargos
    - Diretor: Pode criar Coordenador, Gerente, Franqueado, Sócio Unidade, Captador, Projetista, Financeiro
    - Coordenador: Pode criar Captador, Projetista
    - Gerente: Pode criar Captador, Projetista
    - Franqueado: Pode criar Gerente, Projetista, Captador
    - Sócio Unidade: Pode criar Gerente, Projetista, Captador
    - Financeiro: Não pode criar nenhum cargo
    - Captador: Não pode criar nenhum cargo
    - Projetista: Não pode criar nenhum cargo
    """
    
    # Definição da hierarquia - quais cargos cada cargo pode criar
    ROLE_HIERARCHY = {
        'ceo': ['ceo', 'diretor', 'coordenador', 'gerente', 'franqueado', 'socio_unidade', 'financeiro', 'captador', 'projetista'],
        'diretor': ['coordenador', 'gerente', 'franqueado', 'socio_unidade', 'captador', 'projetista' 'financeiro'],
        'coordenador': ['captador', 'projetista'],
        'franqueado': ['gerente', 'projetista', 'captador'],
        'socio_unidade': ['gerente', 'projetista', 'captador'],
        'gerente': ['captador', 'projetista'],
        'financeiro': [],  # Não pode criar nenhum cargo
        'captador': [],   # Não pode criar nenhum cargo
        'projetista': []  # Não pode criar nenhum cargo
    }
    
    # Obter os códigos dos roles do usuário atual
    user_role_codes = list(user.roles.values_list('code', flat=True))
    
    # Se o usuário não tem nenhum role, não pode criar ninguém
    if not user_role_codes:
        return []
    
    # Coletar todos os cargos que o usuário pode criar
    allowed_roles = set()
    
    for role_code in user_role_codes:
        if role_code in ROLE_HIERARCHY:
            allowed_roles.update(ROLE_HIERARCHY[role_code])
    
    return list(allowed_roles)

def get_role_hierarchy_description(user):
    """
    Retorna uma descrição amigável dos cargos que o usuário pode criar
    """
    from users.models import Role
    
    allowed_role_codes = get_allowed_roles_for_user(user)
    
    if not allowed_role_codes:
        return "Você não tem permissão para criar usuários com cargos."
    
    # Buscar os nomes dos cargos permitidos
    allowed_roles = Role.objects.filter(code__in=allowed_role_codes, is_active=True)
    role_names = [role.name for role in allowed_roles]
    
    if len(role_names) == 1:
        return f"Você pode criar usuários com o cargo: {role_names[0]}"
    elif len(role_names) <= 3:
        return f"Você pode criar usuários com os cargos: {', '.join(role_names)}"
    else:
        return f"Você pode criar usuários com {len(role_names)} cargos diferentes" 