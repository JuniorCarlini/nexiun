from units.models import Unit
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.urls import reverse_lazy
from enterprises.models import Enterprise
from django.core.paginator import Paginator
from users.decorators import permission_required
from users.models import User, Role, SystemModule
from users.utils import get_allowed_roles_for_user
from django.contrib.auth.models import Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login , authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Recuperação de senha
from django.contrib.auth.views import (
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView
)

# Validação de CPF
def is_valid_cpf(cpf):
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # CPF precisa ter 11 dígitos e não pode ser uma sequência repetida (ex: 111.111.111-11)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Calcula o primeiro dígito verificador
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = (sum1 * 10 % 11) % 10
    
    # Calcula o segundo dígito verificador
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = (sum2 * 10 % 11) % 10
    
    # Verifica se os dígitos calculados coincidem com os dígitos do CPF
    return digit1 == int(cpf[9]) and digit2 == int(cpf[10])

# Cadastro de usuário
def register_view(request):
    if request.method == 'GET':
        return render(request, "users/register.html")
    elif request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        cpf = request.POST.get('cpf')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Guarda os dados para que o formulário seja reexibido em caso de erro
        context = {
            'name': name,
            'email': email,
            'cpf': cpf,
        }

        if password1 != password2:
            messages.error(request, 'Senhas não conferem.')
            return render(request, "users/register.html", context)

        if len(password1) < 6:
            messages.error(request, 'Senha muito curta. A senha deve ter pelo menos 6 caracteres.')
            return render(request, "users/register.html", context)

        # Verifica se o CPF é válido
        if not is_valid_cpf(cpf):
            messages.error(request, 'CPF inválido, insira um CPF válido.')
            return render(request, "users/register.html", context)

        # Verifica se o e-mail já existe
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email já cadastrado.')
            return render(request, "users/register.html", context)

        # Verifica se o CPF já existe
        if User.objects.filter(cpf=cpf).exists():
            messages.error(request, 'CPF já cadastrado.')
            return render(request, "users/register.html", context)

        # Cria o usuário se as verificações passarem
        user = User.objects.create_user(email=email, password=password1, name=name, cpf=cpf)
        messages.success(request, 'Usuário cadastrado, faça login!.')
        return redirect("login")

# Login de usuário
def login_view(request):
    # Se o usuário já estiver autenticado, redireciona para a home
    if request.user.is_authenticated:
        return redirect("/")
        
    if request.method == 'GET':
        return render(request, "users/login.html")
        
    elif request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # ANTES da autenticação, verifica se o usuário pertence a uma empresa
        # e se está tentando fazer login no domínio principal
        current_host = request.get_host().lower()
        
        # Remove porta se presente (para desenvolvimento)
        if ':' in current_host:
            current_host = current_host.split(':')[0]
        
        # Se estiver no domínio principal, verifica se o usuário tem empresa
        if current_host in ['nexiun.com.br', 'www.nexiun.com.br', 'nexiun.local', 'localhost', '127.0.0.1']:
            # Só verifica se o email foi fornecido
            if email:
                try:
                    # Busca o usuário pelo email para verificar se tem empresa
                    from users.models import User
                    user_check = User.objects.get(email=email)
                    
                    if user_check.enterprise:
                        # Usuário tem empresa - redireciona para login da empresa
                        messages.info(
                            request, 
                            f'Redirecionando para o login da {user_check.enterprise.name}...'
                        )
                        login_url = f"{user_check.enterprise.get_absolute_url()}/users/login/"
                        return redirect(login_url)
                        
                except User.DoesNotExist:
                    # Usuário não existe - continua com o fluxo normal para mostrar erro
                    pass

        # Autentica o usuário (fluxo normal)
        user = authenticate(request, email=email, password=password)
        
        # Caso a autenticação falhe, mostra mensagem de erro
        if user is None:
            messages.error(request, 'Usuário ou senha incorretos!')
            return render(request, 'users/login.html')
        
        # Realiza o login do usuário
        login(request, user)
        
        # Após o login, verifica se o usuário possui uma empresa
        if user.enterprise is None:
            # Redireciona para a criação de empresa
            return redirect('create_enterprise')
        
        # Se chegou até aqui, significa que está no subdomínio correto
        next_url = request.GET.get('next', '/')
        return redirect(next_url)

# Logout de usuário
def logout_view(request):
    logout(request)
    return redirect('home')

# Configurações do usuário
@login_required
def config_view(request):
    user = request.user
    enterprise = user.enterprise

    if request.method == 'POST':
        # Todos os usuários podem editar seus dados pessoais
        user.name = request.POST.get('name', user.name)
        user.phone = request.POST.get('phone', user.phone)
        user.theme_preference = request.POST.get('theme_preference', user.theme_preference)
        user.cpf = request.POST.get('cpf', user.cpf)
        
        # Email permanece bloqueado para edição (apenas leitura)
        # user.email = request.POST.get('email', user.email)  # Removido
        
        # Atualizar data de nascimento se fornecida
        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            from datetime import datetime
            try:
                user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Data de nascimento inválida.')
                return redirect('config')

        # Verificando se uma nova imagem de perfil foi enviada
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']

        user.save()
        
        # Atualizando dados da empresa apenas se o usuário for CEO
        if enterprise and user.roles.filter(code='ceo', is_active=True).exists():
            enterprise.name = request.POST.get('enterprise_name', enterprise.name)
            enterprise.cnpj_or_cpf = request.POST.get('enterprise_cnpj_or_cpf', enterprise.cnpj_or_cpf)
            enterprise.primary_color = request.POST.get('primary_color', enterprise.primary_color)
            enterprise.secondary_color = request.POST.get('secondary_color', enterprise.secondary_color)
            enterprise.text_icons_color = request.POST.get('text_icons_color', enterprise.text_icons_color)

            # Verificando se novos logotipos da empresa foram enviados
            if request.FILES.get('logo_light'):
                enterprise.logo_light = request.FILES['logo_light']
            
            if request.FILES.get('logo_dark'):
                enterprise.logo_dark = request.FILES['logo_dark']
            
            # Verificando se um novo favicon da empresa foi enviado
            if request.FILES.get('favicon'):
                enterprise.favicon = request.FILES['favicon']

            enterprise.save()

        # Mensagem personalizada se tema foi alterado
        old_theme = User.objects.get(id=user.id).theme_preference
        new_theme = request.POST.get('theme_preference', user.theme_preference)
        
        if old_theme != new_theme:
            theme_names = {'light': 'Claro', 'dark': 'Escuro', 'auto': 'Automático'}
            messages.success(request, f'Configurações salvas! Tema alterado para: {theme_names.get(new_theme, new_theme)}')
        else:
            messages.success(request, 'Dados atualizados com sucesso!')
        
        return redirect('config')

    context = {
        'user': user,
        'enterprise': enterprise,
    }
    return render(request, 'users/config.html', context)

# Criação de usuário
@login_required
@permission_required('users.add_users', 'Você não tem permissão para criar usuários.')
def create_user_view(request):
    user = request.user
    enterprise = user.enterprise
    units = Unit.objects.filter(enterprise=enterprise)
    
    # Buscar roles disponíveis (cargos que o usuário pode atribuir) baseado na hierarquia
    allowed_role_codes = get_allowed_roles_for_user(user)
    
    if not allowed_role_codes:
        # Se o usuário não pode criar nenhum cargo, mostrar mensagem e redirecionar
        messages.error(request, 'Você não tem permissão para criar usuários com qualquer cargo.')
        return redirect('list_users')
    
    available_roles = Role.objects.filter(is_active=True, code__in=allowed_role_codes)
    
    # Buscar módulos do sistema e suas permissões
    system_modules = []
    for module in SystemModule.objects.filter(is_active=True).order_by('order'):
        # Buscar permissões relacionadas a este módulo
        module_permissions = Permission.objects.filter(
            codename__endswith=f'_{module.code}',
            content_type__app_label='users'
        ).order_by('name')
        
        system_modules.append({
            'code': module.code,
            'name': module.name,
            'icon': module.icon,
            'permissions': module_permissions
        })

    context = {
        'units': units,
        'available_roles': available_roles,
        'system_modules': system_modules,
        'enterprise': enterprise,
        'form_data': {}
    }

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        cpf = request.POST.get('cpf', '')
        phone = request.POST.get('phone', '')
        unit_ids = request.POST.getlist('units')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Cargos e permissões selecionados
        selected_roles = request.POST.getlist('roles')
        selected_permissions = request.POST.getlist('custom_permissions')
        
        # Validar se os roles selecionados estão permitidos para este usuário
        if selected_roles:
            selected_role_objects = Role.objects.filter(id__in=selected_roles, is_active=True)
            selected_role_codes = list(selected_role_objects.values_list('code', flat=True))
            
            # Verificar se todos os roles selecionados estão na lista de permitidos
            for role_code in selected_role_codes:
                if role_code not in allowed_role_codes:
                    role_name = selected_role_objects.filter(code=role_code).first()
                    role_name = role_name.name if role_name else role_code
                    messages.error(request, f'Você não tem permissão para atribuir o cargo "{role_name}".')
                    return render(request, 'users/register_user.html', context)
        
        form_data = {
            'name': name,
            'email': email,
            'cpf': cpf,
            'phone': phone,
            'units': unit_ids,
            'roles': selected_roles,
            'custom_permissions': selected_permissions,
        }
        context['form_data'] = form_data

        required_fields = {
            'nome': name,
            'email': email,
            'cpf': cpf,
            'telefone': phone,
            'unidades': unit_ids,
            'cargo': selected_roles,
            'senha': password1,
            'confirmação de senha': password2
        }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            messages.error(request, f'Os seguintes campos são obrigatórios: {", ".join(missing_fields)}')
            return render(request, 'users/register_user.html', context)

        cpf_clean = ''.join(filter(str.isdigit, cpf))
        if not is_valid_cpf(cpf_clean):
            messages.error(request, 'CPF inválido.')
            return render(request, 'users/register_user.html', context)

        phone_clean = ''.join(filter(str.isdigit, phone))
        if len(phone_clean) < 10 or len(phone_clean) > 11:
            messages.error(request, 'Telefone inválido.')
            return render(request, 'users/register_user.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email já cadastrado.')
            return render(request, 'users/register_user.html', context)

        if User.objects.filter(cpf=cpf_clean).exists():
            messages.error(request, 'CPF já cadastrado.')
            return render(request, 'users/register_user.html', context)

        # Validar as unidades selecionadas
        if not unit_ids:
            messages.error(request, 'Selecione pelo menos uma unidade.')
            return render(request, 'users/register_user.html', context)
            
        try:
            selected_units = Unit.objects.filter(id__in=unit_ids, enterprise=enterprise)
            if selected_units.count() != len(unit_ids):
                messages.error(request, 'Uma ou mais unidades são inválidas.')
                return render(request, 'users/register_user.html', context)
        except (ValueError, Unit.DoesNotExist):
            messages.error(request, 'Unidades inválidas.')
            return render(request, 'users/register_user.html', context)

        profile_image = request.FILES.get('logo')
        if profile_image:
            if not profile_image.content_type.startswith('image'):
                messages.error(request, 'Arquivo não é uma imagem válida.')
                return render(request, 'users/register_user.html', context)
            if profile_image.size > 5 * 1024 * 1024:
                messages.error(request, 'Imagem deve ter no máximo 5MB.')
                return render(request, 'users/register_user.html', context)

        if password1 != password2:
            messages.error(request, 'Senhas não coincidem.')
            return render(request, 'users/register_user.html', context)

        if len(password1) < 8:
            messages.error(request, 'Senha deve ter no mínimo 8 caracteres.')
            return render(request, 'users/register_user.html', context)

        try:
            # Criar usuário com novo sistema
            new_user = User(
                name=name,
                email=email,
                cpf=cpf_clean,
                phone=phone_clean,
                profile_image=profile_image,
                enterprise=enterprise
            )
            new_user.set_password(password1)
            new_user.save()
            
            # Atribuir unidades selecionadas
            new_user.units.set(selected_units)
            
            # Atribuir roles selecionados
            if selected_roles:
                roles = Role.objects.filter(id__in=selected_roles, is_active=True)
                new_user.roles.set(roles)
            
            # Atribuir permissões customizadas
            if selected_permissions:
                permissions = Permission.objects.filter(id__in=selected_permissions)
                new_user.custom_permissions.set(permissions)
            
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('list_users')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {str(e)}')
            return render(request, 'users/register_user.html', context)

    return render(request, 'users/register_user.html', context)

# Edição de usuário
@permission_required('users.change_users', 'Você não tem permissão para editar usuários.')
def edit_user_view(request, user_id):
    try:
        edit_user = User.objects.get(id=user_id)
        user = request.user
        enterprise = user.enterprise
        
        if edit_user.is_superuser:
            messages.error(request, 'Sem permissão para editar super admin.')
            return redirect('list_users')
            
        # Verificar se pode editar apenas usuários da sua unidade
        if not user.has_perm('users.change_all_users') and user.unit != edit_user.unit:
            messages.error(request, 'Você só pode editar usuários da sua unidade.')
            return redirect('list_users')

        units = Unit.objects.filter(enterprise=enterprise)
        
        # Buscar roles disponíveis baseado na hierarquia (mesmo sistema da criação)
        allowed_role_codes = get_allowed_roles_for_user(user)
        
        if not allowed_role_codes:
            # Se o usuário não pode atribuir nenhum cargo, mostrar mensagem e redirecionar
            messages.error(request, 'Você não tem permissão para editar cargos de usuários.')
            return redirect('list_users')
        
        available_roles = Role.objects.filter(is_active=True, code__in=allowed_role_codes)
        
        system_modules = []
        for module in SystemModule.objects.filter(is_active=True).order_by('order'):
            module_permissions = Permission.objects.filter(
                codename__endswith=f'_{module.code}',
                content_type__app_label='users'
            ).order_by('name')
            
            system_modules.append({
                'code': module.code,
                'name': module.name,
                'icon': module.icon,
                'permissions': module_permissions
            })

        # IDs dos roles e permissões atuais do usuário
        user_roles = list(edit_user.roles.values_list('id', flat=True))
        user_permissions = list(edit_user.custom_permissions.values_list('id', flat=True))

        context = {
            'edit_user': edit_user,
            'units': units,
            'available_roles': available_roles,
            'system_modules': system_modules,
            'user_roles': user_roles,
            'user_permissions': user_permissions,
            'enterprise': enterprise,
        }
        if request.method == 'POST':
            name = request.POST.get('name')
            email = request.POST.get('email')
            cpf = request.POST.get('cpf')
            phone = request.POST.get('phone')
            unit_ids = request.POST.getlist('units')
            
            # Cargos e permissões selecionados
            selected_roles = request.POST.getlist('roles')
            selected_permissions = request.POST.getlist('custom_permissions')
            
            # Validar se os roles selecionados estão permitidos para este usuário
            if selected_roles:
                selected_role_objects = Role.objects.filter(id__in=selected_roles, is_active=True)
                selected_role_codes = list(selected_role_objects.values_list('code', flat=True))
                
                # Verificar se todos os roles selecionados estão na lista de permitidos
                for role_code in selected_role_codes:
                    if role_code not in allowed_role_codes:
                        role_name = selected_role_objects.filter(code=role_code).first()
                        role_name = role_name.name if role_name else role_code
                        messages.error(request, f'Você não tem permissão para atribuir o cargo "{role_name}".')
                        return render(request, 'users/edit_user.html', context)

            # Validação de email único
            if User.objects.filter(email=email).exclude(id=user_id).exists():
                messages.error(request, 'Email já cadastrado.')
                return render(request, 'users/edit_user.html', context)

            # Validação de CPF único
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            if User.objects.filter(cpf=cpf_clean).exclude(id=user_id).exists():
                messages.error(request, 'CPF já cadastrado.')
                return render(request, 'users/edit_user.html', context)

            phone_clean = ''.join(filter(str.isdigit, phone))
            if len(phone_clean) < 10 or len(phone_clean) > 11:
                messages.error(request, 'Telefone inválido.')
                return render(request, 'users/edit_user.html', context)

            # Validar as unidades selecionadas
            if not unit_ids:
                messages.error(request, 'Selecione pelo menos uma unidade.')
                return render(request, 'users/edit_user.html', context)
                
            try:
                selected_units = Unit.objects.filter(id__in=unit_ids, enterprise=enterprise)
                if selected_units.count() != len(unit_ids):
                    messages.error(request, 'Uma ou mais unidades são inválidas.')
                    return render(request, 'users/edit_user.html', context)
            except (ValueError, Unit.DoesNotExist):
                messages.error(request, 'Unidades inválidas.')
                return render(request, 'users/edit_user.html', context)

            # Atualiza senha se fornecida
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 and password2:
                if password1 != password2:
                    messages.error(request, 'Senhas não coincidem.')
                    return render(request, 'users/edit_user.html', context)
                
                if len(password1) < 8:
                    messages.error(request, 'Senha deve ter no mínimo 8 caracteres.')
                    return render(request, 'users/edit_user.html', context)
                
                edit_user.set_password(password1)

            # Atualiza imagem se fornecida
            profile_image = request.FILES.get('logo')
            if profile_image:
                if not profile_image.content_type.startswith('image'):
                    messages.error(request, 'Arquivo não é uma imagem válida.')
                    return render(request, 'users/edit_user.html', context)
                if profile_image.size > 5 * 1024 * 1024:
                    messages.error(request, 'Imagem deve ter no máximo 5MB.')
                    return render(request, 'users/edit_user.html', context)
                edit_user.profile_image = profile_image

            # Atualiza dados do usuário
            edit_user.name = name
            edit_user.email = email 
            edit_user.cpf = cpf_clean
            edit_user.phone = phone_clean
            edit_user.save()
            
            # Atualizar unidades
            edit_user.units.set(selected_units)
            
            # Atualizar roles e permissões
            if selected_roles:
                roles = Role.objects.filter(id__in=selected_roles, is_active=True)
                edit_user.roles.set(roles)
            else:
                edit_user.roles.clear()
            
            if selected_permissions:
                permissions = Permission.objects.filter(id__in=selected_permissions)
                edit_user.custom_permissions.set(permissions)
            else:
                edit_user.custom_permissions.clear()

            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('list_users')

        return render(request, 'users/edit_user.html', context)

    except User.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('list_users')

# Lista os usuários da empresa
@permission_required('users.view_users', 'Você não tem permissão para visualizar usuários.')
def list_users_view(request):
    # Com o novo sistema, a filtragem pode ser mais flexível
    users = User.objects.filter(is_superuser=False)
    
    # Filtrar por empresa se não for superuser
    if not request.user.is_superuser and request.user.enterprise:
        users = users.filter(enterprise=request.user.enterprise)
    
    # Se o usuário só pode ver usuários da sua unidade
    if request.user.has_perm('users.view_unit_users') and not request.user.has_perm('users.view_all_users'):
        user_units = request.user.units.all()
        if user_units.exists():
            users = users.filter(units__in=user_units)

    # Ordenar os usuários para evitar warning de paginação inconsistente
    users = users.order_by('name', 'id')

    paginator = Paginator(users, 20)
    users_page = paginator.get_page(request.GET.get("page"))

    return render(request, "users/list_users.html", {"users": users_page})

# Recuperação de senha
class PasswordResetView(DjangoPasswordResetView):
    template_name = 'password_reset/password_reset_form.html'
    email_template_name = 'password_reset/password_reset_email.html'
    subject_template_name = 'password_reset/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

class PasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = 'password_reset/password_reset_done.html'

class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = 'password_reset/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        # Salva a nova senha
        form.save()
        
        # Adiciona mensagem de sucesso
        messages.success(self.request, 'Sua senha foi alterada com sucesso!')
        return redirect(self.success_url)

class PasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = 'password_reset/password_reset_complete.html'