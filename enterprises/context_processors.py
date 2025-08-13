def custom_context(request):
    user = request.user
    first_name = user.name.split()[0] if user.is_authenticated else ""
    enterprise = user.enterprise if user.is_authenticated else None
    
    # Empresa atual baseada no subdomínio (definida pelo middleware)
    current_enterprise = getattr(request, 'current_enterprise', None)
    
    # Se estamos em um subdomínio específico, usar a empresa do subdomínio
    if current_enterprise:
        enterprise = current_enterprise
    
    # Obter cargos do usuário para exibir no template
    user_roles = []
    if user.is_authenticated:
        user_roles = [role.name for role in user.roles.filter(is_active=True)]

    # Informações de subdomínio
    subdomain_info = {}
    if enterprise:
        subdomain_info = {
            'subdomain': enterprise.subdomain,
            'full_domain': enterprise.get_full_domain(),
            'absolute_url': enterprise.get_absolute_url(),
        }

    return {
        'first_name': first_name,
        'user_roles': user_roles,
        'enterprise': enterprise,
        'current_enterprise': current_enterprise,
        'subdomain_info': subdomain_info,
        'is_subdomain_access': current_enterprise is not None,
    }