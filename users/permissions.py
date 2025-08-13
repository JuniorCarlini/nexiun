from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Definição dos módulos e suas permissões
SYSTEM_MODULES = {
    'usuarios': {
        'name': 'Usuários',
        'icon': 'bi-people-fill',
        'permissions': [
            ('view_users', 'Visualizar usuários'),
            ('add_users', 'Adicionar usuários'),
            ('change_users', 'Editar usuários'),
            ('delete_users', 'Excluir usuários'),
            ('manage_roles_users', 'Gerenciar cargos de usuários'),
            ('view_all_users', 'Ver todos os usuários da empresa'),
            ('change_all_users', 'Editar usuários de todas as unidades'),
        ]
    },
    'projetos': {
        'name': 'Projetos',
        'icon': 'bi-folder-fill',
        'permissions': [
            ('view_projects', 'Visualizar projetos'),
            ('add_projects', 'Adicionar projetos'),
            ('change_projects', 'Editar projetos'),
            ('delete_projects', 'Excluir projetos'),
            ('approve_projects', 'Aprovar projetos'),
            ('finalize_projects', 'Finalizar projetos'),
            ('view_all_projects', 'Ver todos os projetos da empresa'),
            ('view_unit_projects', 'Ver projetos da unidade'),
            ('view_own_projects', 'Ver apenas próprios projetos'),
            ('view_project_payments', 'Visualizar esteira de pagamentos'),
            ('change_project_payments', 'Confirmar pagamentos de projetos'),
            ('change_project_finalize', 'Finalizar projetos (última fase)'),
        ]
    },
    'financeiro': {
        'name': 'Financeiro',
        'icon': 'bi-cash-stack',
        'permissions': [
            ('view_financial', 'Visualizar dados financeiros'),
            ('add_financial', 'Adicionar registros financeiros'),
            ('change_financial', 'Editar registros financeiros'),
            ('delete_financial', 'Excluir registros financeiros'),
            ('view_reports_financial', 'Visualizar relatórios financeiros'),
            ('export_reports_financial', 'Exportar relatórios financeiros'),
            ('view_banks', 'Visualizar bancos'),
            ('add_banks', 'Adicionar bancos'),
            ('change_banks', 'Editar bancos'),
            ('delete_banks', 'Excluir bancos'),
            ('view_credit_lines', 'Visualizar linhas de crédito'),
            ('add_credit_lines', 'Adicionar linhas de crédito'),
            ('change_credit_lines', 'Editar linhas de crédito'),
            ('delete_credit_lines', 'Excluir linhas de crédito'),
        ]
    },
    'clientes': {
        'name': 'Clientes',
        'icon': 'bi-person-badge-fill',
        'permissions': [
            ('view_clients', 'Visualizar clientes'),
            ('add_clients', 'Adicionar clientes'),
            ('change_clients', 'Editar clientes'),
            ('delete_clients', 'Excluir clientes'),
            ('view_all_clients', 'Ver todos os clientes da empresa'),
            ('view_unit_clients', 'Ver clientes da unidade'),
        ]
    },
    'unidades': {
        'name': 'Unidades',
        'icon': 'bi-building-fill',
        'permissions': [
            ('view_units', 'Visualizar unidades'),
            ('add_units', 'Adicionar unidades'),
            ('change_units', 'Editar unidades'),
            ('delete_units', 'Excluir unidades'),
            ('view_unit_transactions', 'Visualizar transações da unidade'),
            ('add_unit_transactions', 'Adicionar transações da unidade'),
            ('change_unit_transactions', 'Editar transações da unidade'),
            ('delete_unit_transactions', 'Excluir transações da unidade'),
            ('view_all_unit_transactions', 'Ver transações de todas as unidades'),
            ('view_unit_financial_dashboard', 'Ver dashboard financeiro da unidade'),
        ]
    },
    'relatorios': {
        'name': 'Relatórios',
        'icon': 'bi-bar-chart-fill',
        'permissions': [
            ('view_reports', 'Visualizar relatórios'),
            ('export_reports', 'Exportar relatórios'),
            ('view_advanced_reports', 'Visualizar relatórios avançados'),
            ('create_custom_reports', 'Criar relatórios customizados'),
        ]
    },
    'configuracoes': {
        'name': 'Configurações',
        'icon': 'bi-gear-fill',
        'permissions': [
            ('view_settings', 'Visualizar configurações'),
            ('change_settings', 'Alterar configurações'),
            ('manage_enterprise_settings', 'Gerenciar configurações da empresa'),
            ('manage_system_settings', 'Gerenciar configurações do sistema'),
        ]
    },
    'dashboard': {
        'name': 'Dashboard',
        'icon': 'bi-speedometer2',
        'permissions': [
            ('view_dashboard', 'Visualizar dashboard'),
    
            ('view_company_dashboard', 'Ver dashboard da empresa'),
            ('view_unit_dashboard', 'Ver dashboard da unidade'),
        ]
    }
}

# Definição dos cargos padrão e suas permissões
DEFAULT_ROLES = {
    'ceo': {
        'name': 'CEO',
        'permissions': [
            # Todas as permissões - CEO tem acesso total
            'users.view_users', 'users.add_users', 'users.change_users', 
            'users.delete_users', 'users.manage_roles_users',
            'users.view_all_users', 'users.change_all_users',
            'users.view_projects', 'users.add_projects', 'users.change_projects', 
            'users.delete_projects', 'users.approve_projects', 'users.finalize_projects',
            'users.view_all_projects', 'users.view_project_payments', 
            'users.change_project_payments', 'users.change_project_finalize',
            'users.view_financial', 'users.add_financial', 'users.change_financial',
            'users.delete_financial', 'users.view_reports_financial', 'users.export_reports_financial',
            'users.view_banks', 'users.add_banks', 'users.change_banks', 'users.delete_banks',
            'users.view_credit_lines', 'users.add_credit_lines', 'users.change_credit_lines', 'users.delete_credit_lines',
            'users.view_clients', 'users.add_clients', 'users.change_clients', 
            'users.delete_clients', 'users.view_all_clients',
            'users.view_units', 'users.add_units', 'users.change_units', 'users.delete_units',
            'users.view_unit_transactions', 'users.add_unit_transactions', 'users.change_unit_transactions', 
            'users.delete_unit_transactions', 'users.view_all_unit_transactions', 'users.view_unit_financial_dashboard',
            'users.view_reports', 'users.export_reports', 'users.view_advanced_reports',
            'users.create_custom_reports',
            'users.view_settings', 'users.change_settings', 
            'users.manage_enterprise_settings', 'users.manage_system_settings',
            'users.view_dashboard', 'users.view_company_dashboard',
        ]
    },
    'diretor': {
        'name': 'Diretor',
        'permissions': [
            'users.view_users', 'users.add_users', 'users.change_users',
            'users.view_projects', 'users.add_projects', 'users.change_projects', 
            'users.approve_projects', 'users.view_all_projects', 'users.view_project_payments',
            'users.change_project_payments', 'users.change_project_finalize',
            'users.view_financial', 'users.view_reports_financial', 'users.export_reports_financial',
            'users.view_banks', 'users.add_banks', 'users.change_banks',
            'users.view_credit_lines', 'users.add_credit_lines', 'users.change_credit_lines',
            'users.view_clients', 'users.add_clients', 'users.change_clients', 'users.view_all_clients',
            'users.view_units', 'users.change_units',
            'users.view_unit_transactions', 'users.add_unit_transactions', 'users.change_unit_transactions',
            'users.view_all_unit_transactions', 'users.view_unit_financial_dashboard',
            'users.view_reports', 'users.export_reports', 'users.view_advanced_reports',
            'users.view_settings',
            'users.view_dashboard', 'users.view_company_dashboard',
        ]
    },
    'gerente': {
        'name': 'Gerente',
        'permissions': [
            'users.view_users',
            'users.view_projects', 'users.add_projects', 'users.change_projects', 'users.view_all_projects',
            'users.view_financial', 'users.view_reports_financial',
            'users.view_clients', 'users.add_clients', 'users.change_clients', 'users.view_all_clients',
            'users.view_units',
            'users.view_unit_transactions', 'users.view_all_unit_transactions', 'users.view_unit_financial_dashboard',
            'users.view_reports', 'users.export_reports',
            'users.view_dashboard', 'users.view_company_dashboard',
        ]
    },
    'socio_unidade': {
        'name': 'Sócio Unidade',
        'permissions': [
            'users.view_users',
            'users.view_projects', 'users.add_projects', 'users.change_projects', 'users.view_unit_projects',
            'users.view_financial',
            'users.view_clients', 'users.add_clients', 'users.change_clients', 'users.view_unit_clients',
            'users.view_reports',
            'users.view_unit_transactions', 'users.add_unit_transactions', 'users.change_unit_transactions', 'users.view_unit_financial_dashboard',
            'users.view_dashboard', 'users.view_unit_dashboard',
        ]
    },
    'franqueado': {
        'name': 'Franqueado',
        'permissions': [
            'users.view_users',
            'users.view_projects', 'users.add_projects', 'users.change_projects', 'users.view_unit_projects',
            'users.view_financial',
            'users.view_clients', 'users.add_clients', 'users.change_clients', 'users.view_unit_clients',
            'users.view_reports',
            'users.view_unit_transactions', 'users.add_unit_transactions', 'users.change_unit_transactions', 'users.view_unit_financial_dashboard',
            'users.view_dashboard', 'users.view_unit_dashboard',
        ]
    },
    'financeiro': {
        'name': 'Financeiro',
        'permissions': [
            'users.view_projects', 'users.view_project_payments', 
            'users.change_project_payments', 'users.change_project_finalize',
            'users.view_financial', 'users.add_financial', 'users.change_financial',
            'users.view_reports_financial', 'users.export_reports_financial',
            'users.view_clients',
            'users.view_reports', 'users.export_reports',
            'users.view_dashboard',
        ]
    },
    'coordenador': {
        'name': 'Coordenador',
        'permissions': [
            'users.view_projects', 'users.add_projects', 'users.change_projects', 'users.view_unit_projects',
            'users.view_clients', 'users.add_clients', 'users.change_clients', 'users.view_unit_clients',
            'users.view_reports',
            'users.view_dashboard', 'users.view_unit_dashboard',
        ]
    },
    'projetista': {
        'name': 'Projetista',
        'permissions': [
            'users.view_projects', 'users.add_projects', 'users.change_projects', 'users.view_own_projects',
            'users.view_clients', 'users.add_clients', 'users.change_clients', 
            'users.delete_clients', 'users.view_unit_clients',
            'users.view_dashboard',
        ]
    },
    'captador': {
        'name': 'Captador',
        'permissions': [
            'users.view_projects', 'users.add_projects', 'users.view_own_projects',
            'users.view_clients', 'users.add_clients', 'users.change_clients',
            'users.view_dashboard',
        ]
    }
}

def create_custom_permissions():
    """Cria as permissões customizadas do sistema"""
    from users.models import User
    
    # Obtém o content type para User (pode ser usado para todas as permissões customizadas)
    content_type = ContentType.objects.get_for_model(User)
    
    created_permissions = []
    
    for module_code, module_data in SYSTEM_MODULES.items():
        for perm_code, perm_name in module_data['permissions']:
            permission, created = Permission.objects.get_or_create(
                codename=perm_code,
                content_type=content_type,
                defaults={'name': perm_name}
            )
            if created:
                created_permissions.append(permission)
    
    return created_permissions

def create_system_modules():
    """Cria os módulos do sistema"""
    from users.models import SystemModule
    
    created_modules = []
    
    for i, (module_code, module_data) in enumerate(SYSTEM_MODULES.items()):
        module, created = SystemModule.objects.get_or_create(
            code=module_code,
            defaults={
                'name': module_data['name'],
                'icon': module_data['icon'],
                'order': i * 10,
                'description': f'Módulo {module_data["name"]} do sistema'
            }
        )
        if created:
            created_modules.append(module)
    
    return created_modules

def create_default_roles():
    """Cria os cargos padrão do sistema"""
    from users.models import Role
    
    created_roles = []
    
    for role_code, role_data in DEFAULT_ROLES.items():
        role, created = Role.objects.get_or_create(
            code=role_code,
            defaults={
                'name': role_data['name'],
                'description': f'Cargo {role_data["name"]} com permissões padrão'
            }
        )
        
        if created or not role.permissions.exists():
            # Adiciona as permissões ao cargo
            permissions = []
            for perm_name in role_data['permissions']:
                app_label, codename = perm_name.split('.')
                try:
                    # Buscar primeiro pela app_label correto (users para as permissões customizadas)
                    permission = Permission.objects.get(
                        codename=codename,
                        content_type__app_label='users'
                    )
                    permissions.append(permission)
                except Permission.DoesNotExist:
                    # Se não encontrar, tentar pela app_label original
                    try:
                        permission = Permission.objects.get(
                            codename=codename,
                            content_type__app_label=app_label
                        )
                        permissions.append(permission)
                    except Permission.DoesNotExist:
                        print(f"Permissão não encontrada: {perm_name}")
            
            role.permissions.set(permissions)
            
        if created:
            created_roles.append(role)
    
    return created_roles 