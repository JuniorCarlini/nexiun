import os
from datetime import date
from units.models import Unit
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from projects.models import Project
from .models import InternalMessage
from django.http import JsonResponse
from .utils import calculate_parcelas 
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.templatetags.static import static
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from enterprises.models import Enterprise , Client, ClientDocument
from projects.models import Project, User, CreditLine, Bank, ProjectDocument, ProjectHistory, PROJECT_STATUS_CHOICES, ACTIVITY_CHOICES, SIZE_CHOICES


# Criar empresa
@login_required
def create_enterprise(request):
    context = {
        'enterprise': getattr(request.user, 'enterprise', None),
        'primary_color': '#05677D',
        'secondary_color': '#FFB845',
        'text_icons_color': '#FFFFFF',
    }
    
    if request.method == 'POST':
        name = request.POST.get('name')
        cnpj_or_cpf = request.POST.get('cnpj_or_cpf')
        subdomain = request.POST.get('subdomain', '').strip().lower()
        primary_color = request.POST.get('primary_color', '#05677D')
        secondary_color = request.POST.get('secondary_color', '#FFB845')
        text_icons_color = request.POST.get('text_icons_color', '#FFFFFF')
        logo_light = request.FILES.get('logo_light')
        logo_dark = request.FILES.get('logo_dark')
        
        # Validações
        errors = []
        
        if not name:
            errors.append("Nome da empresa é obrigatório.")
        
        if not cnpj_or_cpf:
            errors.append("CNPJ/CPF é obrigatório.")
        
        # Validar subdomínio se fornecido
        if subdomain:
            try:
                from .models import validate_subdomain
                validate_subdomain(subdomain)
                
                # Verificar se já existe
                if Enterprise.objects.filter(subdomain=subdomain).exists():
                    errors.append(f"O subdomínio '{subdomain}' já está em uso.")
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            for error in errors:
                messages.error(request, error)
            # Preservar valores digitados pelo usuário
            context.update({
                'name': name,
                'cnpj_or_cpf': cnpj_or_cpf,
                'subdomain': subdomain,
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'text_icons_color': text_icons_color,
            })
            return render(request, 'enterprises/create_enterprise.html', context)
        
        try:
            # Criar a empresa
            enterprise_data = {
                'name': name,
                'cnpj_or_cpf': cnpj_or_cpf,
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'text_icons_color': text_icons_color,
            }
            
            # Adicionar subdomínio se fornecido
            if subdomain:
                enterprise_data['subdomain'] = subdomain
            
            # Adicionar logos apenas se foram enviados
            if logo_light:
                enterprise_data['logo_light'] = logo_light
            
            if logo_dark:
                enterprise_data['logo_dark'] = logo_dark
                
            enterprise = Enterprise.objects.create(**enterprise_data)
            
            # Atribuir empresa e cargo CEO ao usuário
            request.user.enterprise = enterprise
            request.user.save()
            
            # Atribuir role CEO com todas as permissões
            from users.models import Role
            try:
                ceo_role = Role.objects.get(code='ceo', is_active=True)
                request.user.roles.add(ceo_role)
                
                # Mensagem de sucesso com informações do subdomínio
                success_message = f"Empresa criada com sucesso! Você agora é CEO com todos os acessos.<br>"
                success_message += f"<strong>Seu subdomínio:</strong> {enterprise.get_full_domain()}<br>"
                success_message += f"<strong>URL de acesso:</strong> <a href='{enterprise.get_absolute_url()}' target='_blank'>{enterprise.get_absolute_url()}</a>"
                
                messages.success(request, success_message, extra_tags='safe')
                
            except Role.DoesNotExist:
                messages.warning(request, "Empresa criada, mas role CEO não encontrado. Configure via admin.")
            
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f"Erro ao criar empresa: {str(e)}")
            # Preservar valores digitados pelo usuário
            context.update({
                'name': name,
                'cnpj_or_cpf': cnpj_or_cpf,
                'subdomain': subdomain,
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'text_icons_color': text_icons_color,
            })
            return render(request, 'enterprises/create_enterprise.html', context)

    return render(request, 'enterprises/create_enterprise.html', context)

# Registrar cliente
@login_required
def register_client_view(request):
    # Verificar permissão para adicionar clientes
    if not request.user.has_perm('users.add_clients'):
        messages.error(request, 'Você não tem permissão para cadastrar clientes.')
        return redirect('list_clients')
    
    # Verificar se o usuário tem unidades associadas
    user_units = request.user.units.all()
    if not user_units.exists():
        messages.error(request, "Você precisa estar vinculado a pelo menos uma unidade para cadastrar clientes.")
        return redirect('list_clients')

    # Preparar contexto
    from .models import CLIENT_STATUS_CHOICES, PRODUCER_CLASSIFICATION_CHOICES, ACTIVITY_CHOICES
    context = {
        'enterprise': request.user.enterprise,
        'client_documents': [],
        'is_completed': False,
        'user_units': user_units,
        'status_choices': CLIENT_STATUS_CHOICES,
        'producer_classification_choices': PRODUCER_CLASSIFICATION_CHOICES,
        'activity_choices': ACTIVITY_CHOICES,
        'has_multiple_units': user_units.count() > 1,
        'single_unit': user_units.first() if user_units.count() == 1 else None
    }

    if request.method == "POST":
        try:
            # Validações básicas
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            
            if not name:
                messages.error(request, 'O nome é obrigatório.')
                return render(request, 'enterprises/register_client.html', context)
            
            if not email:
                messages.error(request, 'O email é obrigatório.')
                return render(request, 'enterprises/register_client.html', context)
            
            # Verificar se email já existe
            if Client.objects.filter(email=email).exists():
                messages.error(request, f'Já existe um cliente cadastrado com o email "{email}". Por favor, use um email diferente.')
                return render(request, 'enterprises/register_client.html', context)
            
            # Tratar campo de data de nascimento
            date_of_birth = request.POST.get('date_of_birth')
            if not date_of_birth or not date_of_birth.strip():
                date_of_birth = None
                
            # Validar campo "Retorno até" quando status é "EM_NEGOCIACAO"
            status = request.POST.get('status', 'INATIVO')
            retorno_ate = request.POST.get('retorno_ate')
            
            if status == 'EM_NEGOCIACAO':
                if not retorno_ate or not retorno_ate.strip():
                    messages.error(request, 'O campo "Retorno até" é obrigatório quando o cliente está em negociação.')
                    return render(request, 'enterprises/register_client.html', context)
                
                # Validar se a data está dentro do limite de 5 dias
                from datetime import datetime, timedelta
                try:
                    data_retorno = datetime.strptime(retorno_ate, '%Y-%m-%d').date()
                    data_limite = date.today() + timedelta(days=5)
                    
                    if data_retorno < date.today():
                        messages.error(request, 'A data de retorno não pode ser anterior à data atual.')
                        return render(request, 'enterprises/register_client.html', context)
                    
                    if data_retorno > data_limite:
                        messages.error(request, 'A data de retorno não pode ser superior a 5 dias a partir de hoje.')
                        return render(request, 'enterprises/register_client.html', context)
                        
                except ValueError:
                    messages.error(request, 'Data de retorno inválida.')
                    return render(request, 'enterprises/register_client.html', context)
            
            # Preparar retorno_ate para o banco
            if not retorno_ate or not retorno_ate.strip():
                retorno_ate = None
            
            # Cria o cliente com a unidade do usuário logado
            client = Client.objects.create(
                name=name,
                email=email,
                cpf=request.POST.get('cpf', '').strip() or None,
                phone=request.POST.get('phone', '').strip(),
                address=request.POST.get('address', '').strip(),
                city=request.POST.get('city', '').strip(),
                date_of_birth=date_of_birth,
                observations=request.POST.get('observations', '').strip(),
                producer_classification=request.POST.get('producer_classification', '').strip() or None,
                property_area=request.POST.get('property_area', '').strip() or None,
                activity=request.POST.get('activity', '').strip() or None,
                status=status,
                retorno_ate=retorno_ate,
                enterprise=request.user.enterprise,
                created_by=request.user
            )
            
            # Associar cliente à unidade selecionada ou todas as unidades do usuário
            selected_unit_id = request.POST.get('unit_id')
            if selected_unit_id and user_units.filter(id=selected_unit_id).exists():
                # Se uma unidade específica foi selecionada, usa apenas ela
                client.units.set([selected_unit_id])
            elif user_units.exists():
                # Se não selecionou unidade específica ou usuário tem apenas uma unidade
                client.units.set(user_units)

            messages.success(request, f"Cliente '{client.name}' cadastrado com sucesso!")
            return redirect('list_clients')
            
        except ValueError as e:
            if 'date' in str(e).lower():
                messages.error(request, 'Data de nascimento inválida. Use o formato DD/MM/AAAA.')
            else:
                messages.error(request, f'Dados inválidos: {str(e)}')
            return render(request, 'enterprises/register_client.html', context)
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                messages.error(request, 'Este email já está sendo usado por outro cliente.')
            else:
                messages.error(request, f'Erro ao cadastrar cliente: {str(e)}')
            return render(request, 'enterprises/register_client.html', context)
    
    return render(request, 'enterprises/register_client.html', context)

# Visualizar cliente
@login_required
def view_client_view(request, client_id):
    # Verificar permissão para visualizar clientes
    if not request.user.has_perm('users.view_clients'):
        messages.error(request, 'Você não tem permissão para visualizar clientes.')
        return redirect('list_clients')
    
    try:
        # Buscar cliente baseado nas permissões
        client_filter = {
            'id': client_id,
            'enterprise': request.user.enterprise
        }
        
        # Se o usuário só pode ver clientes das suas unidades
        if request.user.has_perm('users.view_unit_clients') and not request.user.has_perm('users.view_all_clients'):
            user_units = request.user.units.all()
            if user_units.exists():
                client = get_object_or_404(Client, id=client_id, enterprise=request.user.enterprise, units__in=user_units)
            else:
                messages.error(request, 'Você não está associado a nenhuma unidade.')
                return redirect('list_clients')
        else:
            client = get_object_or_404(Client, **client_filter)

        if request.method == "POST":
            # Verificar permissão para alterar clientes
            if not request.user.has_perm('users.change_clients'):
                messages.error(request, 'Você não tem permissão para alterar clientes.')
                return redirect('view_client', client_id=client.id)
            
            # Lógica de exclusão de documento
            if "delete_document" in request.POST:
                try:
                    document_id = request.POST.get("document_id")
                    
                    if not document_id:
                        messages.error(request, "ID do documento não fornecido")
                        return redirect('view_client', client_id=client.id)
                    
                    document = ClientDocument.objects.filter(
                        id=document_id,
                        client=client
                    ).first()
                    
                    if not document:
                        messages.error(request, "Documento não encontrado")
                        return redirect('view_client', client_id=client.id)
                    
                    file_name = document.file_name
                    document.delete()
                    messages.success(request, f"Documento '{file_name}' excluído com sucesso!")
                    return redirect('view_client', client_id=client.id)
                
                except Exception as e:
                    messages.error(request, f"Erro ao excluir documento: {str(e)}")
                    return redirect('view_client', client_id=client.id)
            
            # Lógica de gerenciamento de contas bancárias
            elif "action" in request.POST and request.POST["action"] in ["add_bank_account", "edit_bank_account", "delete_bank_account"]:
                try:
                    action = request.POST.get("action")
                    
                    if action == "add_bank_account":
                        from .models import ClientBankAccount
                        from projects.models import Bank
                        
                        bank_id = request.POST.get("bank")
                        agency = request.POST.get("agency", "").strip()
                        account_number = request.POST.get("account_number", "").strip()
                        account_type = request.POST.get("account_type", "CORRENTE")
                        
                        if not all([bank_id, agency, account_number]):
                            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
                            return redirect('view_client', client_id=client.id)
                        
                        try:
                            bank = Bank.objects.get(id=bank_id, enterprise=request.user.enterprise)
                        except Bank.DoesNotExist:
                            messages.error(request, "Banco não encontrado.")
                            return redirect('view_client', client_id=client.id)
                        
                        # Verificar se já existe conta igual
                        existing_account = ClientBankAccount.objects.filter(
                            client=client,
                            bank=bank,
                            agency=agency,
                            account_number=account_number
                        ).first()
                        
                        if existing_account:
                            messages.error(request, "Esta conta bancária já está cadastrada para este cliente.")
                            return redirect('view_client', client_id=client.id)
                        
                        account = ClientBankAccount.objects.create(
                            client=client,
                            bank=bank,
                            agency=agency,
                            account_number=account_number,
                            account_type=account_type,
                            created_by=request.user
                        )
                        
                        messages.success(request, f"Conta bancária {account.get_formatted_account()} adicionada com sucesso!")
                        return redirect('view_client', client_id=client.id)
                    
                    elif action == "delete_bank_account":
                        from .models import ClientBankAccount
                        
                        account_id = request.POST.get("account_id")
                        if not account_id:
                            messages.error(request, "ID da conta não fornecido")
                            return redirect('view_client', client_id=client.id)
                        
                        account = ClientBankAccount.objects.filter(
                            id=account_id,
                            client=client
                        ).first()
                        
                        if not account:
                            messages.error(request, "Conta bancária não encontrada")
                            return redirect('view_client', client_id=client.id)
                        
                        account_name = account.get_formatted_account()
                        account.delete()
                        messages.success(request, f"Conta bancária '{account_name}' excluída com sucesso!")
                        return redirect('view_client', client_id=client.id)
                
                except Exception as e:
                    messages.error(request, f"Erro ao processar conta bancária: {str(e)}")
                    return redirect('view_client', client_id=client.id)
            
            # Lógica de atualização do cliente e upload de documentos
            else:
                try:
                    # Atualizar dados do cliente
                    client.name = request.POST.get('name', client.name)
                    client.email = request.POST.get('email', client.email)
                    client.cpf = request.POST.get('cpf', '').strip() or None
                    client.phone = request.POST.get('phone', client.phone)
                    client.address = request.POST.get('address', client.address)
                    client.city = request.POST.get('city', client.city)
                    client.producer_classification = request.POST.get('producer_classification', '').strip() or None
                    client.property_area = request.POST.get('property_area', '').strip() or None
                    client.activity = request.POST.get('activity', '').strip() or None
                    # Validar campo "Retorno até" quando status é "EM_NEGOCIACAO"
                    new_status = request.POST.get('status', client.status)
                    retorno_ate = request.POST.get('retorno_ate')
                    
                    if new_status == 'EM_NEGOCIACAO':
                        if not retorno_ate or not retorno_ate.strip():
                            messages.error(request, 'O campo "Retorno até" é obrigatório quando o cliente está em negociação.')
                            return redirect('view_client', client_id=client.id)
                        
                        # Validar se a data está dentro do limite de 5 dias
                        from datetime import datetime, timedelta
                        try:
                            data_retorno = datetime.strptime(retorno_ate, '%Y-%m-%d').date()
                            data_limite = date.today() + timedelta(days=5)
                            
                            if data_retorno < date.today():
                                messages.error(request, 'A data de retorno não pode ser anterior à data atual.')
                                return redirect('view_client', client_id=client.id)
                            
                            if data_retorno > data_limite:
                                messages.error(request, 'A data de retorno não pode ser superior a 5 dias a partir de hoje.')
                                return redirect('view_client', client_id=client.id)
                                
                        except ValueError:
                            messages.error(request, 'Data de retorno inválida.')
                            return redirect('view_client', client_id=client.id)
                    
                    client.status = new_status
                    
                    # Preparar retorno_ate para o banco
                    if not retorno_ate or not retorno_ate.strip():
                        client.retorno_ate = None
                    else:
                        client.retorno_ate = retorno_ate
                    
                    # Tratar campo de data de nascimento (pode estar vazio)
                    date_of_birth = request.POST.get('date_of_birth')
                    if date_of_birth and date_of_birth.strip():
                        client.date_of_birth = date_of_birth
                    elif not date_of_birth or not date_of_birth.strip():
                        client.date_of_birth = None
                    
                    client.observations = request.POST.get('observations', client.observations)
                    client.save()

                    # Processar os novos documentos
                    files = request.FILES.getlist('documents[]')
                    uploaded_count = 0
                    
                    for file in files:
                        # Validar tamanho do arquivo (5MB)
                        if file.size > 5 * 1024 * 1024:
                            messages.warning(
                                request, 
                                f"O arquivo {file.name} excede o limite de 5MB e não foi salvo"
                            )
                            continue

                        # Validar tipo do arquivo
                        file_type = file.content_type
                        if file_type not in ['application/pdf', 'image/jpeg', 'image/png']:
                            messages.warning(
                                request, 
                                f"O arquivo {file.name} não é um tipo permitido (PDF, JPG, PNG) e não foi salvo"
                            )
                            continue

                        # Criar o documento
                        ClientDocument.objects.create(
                            client=client,
                            file=file,
                            file_name=file.name,
                            file_type=file_type,
                            file_size=file.size
                        )
                        uploaded_count += 1

                    if uploaded_count > 0:
                        messages.success(request, f"Cliente atualizado! {uploaded_count} documento(s) adicionado(s) com sucesso!")
                    else:
                        messages.success(request, "Cliente atualizado com sucesso!")
                    
                    return redirect('view_client', client_id=client.id)

                except Exception as e:
                    messages.error(request, f"Erro ao atualizar cliente: {str(e)}")
                    return redirect('view_client', client_id=client.id)

        from .models import CLIENT_STATUS_CHOICES, PRODUCER_CLASSIFICATION_CHOICES, ACTIVITY_CHOICES
        from projects.models import Bank
        
        # Buscar histórico do cliente
        client_history = client.history.all().order_by('-timestamp')[:20]  # Últimas 20 alterações
        
        # Buscar bancos disponíveis para o formulário de conta bancária
        available_banks = Bank.objects.filter(enterprise=request.user.enterprise, is_active=True).order_by('name')
        
        context = {
            'enterprise': request.user.enterprise,
            'client': client,
            'client_documents': client.documents.all(),
            'client_history': client_history,
            'projects': [],
            'today': date.today(),
            'status_choices': CLIENT_STATUS_CHOICES,
            'producer_classification_choices': PRODUCER_CLASSIFICATION_CHOICES,
            'activity_choices': ACTIVITY_CHOICES,
            'available_banks': available_banks
        }
        return render(request, 'enterprises/view_client.html', context)
        
    except Exception as e:
        messages.error(request, f"Erro ao carregar página: {str(e)}")
        return redirect('list_clients')

# Listar clientes
@login_required
def client_list_view(request):
    # Verificar permissão básica para visualizar clientes
    if not request.user.has_perm('users.view_clients'):
        messages.error(request, 'Você não tem permissão para visualizar clientes.')
        return redirect('home')
    
    from .models import CLIENT_STATUS_CHOICES
    
    clients = Client.objects.filter(enterprise=request.user.enterprise)
    
    # Filtrar por permissões específicas
    if request.user.has_perm('users.view_unit_clients') and not request.user.has_perm('users.view_all_clients'):
        # Ver apenas clientes das suas unidades
        user_units = request.user.units.all()
        if user_units.exists():
            clients = clients.filter(units__in=user_units)
    
    # Filtros
    status_filter = request.GET.get('status', '')
    search_filter = request.GET.get('search', '')
    
    if status_filter:
        clients = clients.filter(status=status_filter)
    
    if search_filter:
        clients = clients.filter(name__icontains=search_filter)
    
    clients = clients.order_by('-is_active', 'name')  # Ativos primeiro, depois por nome
    paginator = Paginator(clients, 15)
    page = request.GET.get('page', 1)

    try:
        clients_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        clients_page = paginator.page(1)

    return render(request, 'enterprises/list_clients.html', {
        'clients': clients_page,
        'status_choices': CLIENT_STATUS_CHOICES,
        'current_status': status_filter,
        'current_search': search_filter,
    })

# Ativar/Desativar cliente
@login_required
def toggle_client_status_view(request, client_id):
    # Verificar se o usuário tem permissão para alterar clientes
    if not request.user.has_perm('users.change_clients'):
        messages.error(request, 'Você não tem permissão para alterar clientes.')
        return redirect('list_clients')
    
    # Buscar cliente baseado nas permissões
    client_filter = {
        'id': client_id,
        'enterprise': request.user.enterprise
    }
    
    # Se o usuário só pode alterar clientes das suas unidades
    if request.user.has_perm('users.view_unit_clients') and not request.user.has_perm('users.view_all_clients'):
        user_units = request.user.units.all()
        if user_units.exists():
            client = get_object_or_404(Client, id=client_id, enterprise=request.user.enterprise, units__in=user_units)
        else:
            messages.error(request, 'Você não está associado a nenhuma unidade.')
            return redirect('list_clients')
    else:
        client = get_object_or_404(Client, **client_filter)
    
    if request.method == 'POST':
        # Alterna o status do cliente
        client.is_active = not client.is_active
        client.save()
        
        status_text = "ativado" if client.is_active else "desativado"
        messages.success(request, f'Cliente "{client.name}" foi {status_text} com sucesso!')
    
    return redirect('list_clients')

# Visualizar projeto do cliente
@login_required
def client_project_details_view(request, project_id):
    context = {
        'enterprise': request.user.enterprise,
    }
    return render(request, 'enterprises/client_project_details.html', context)

# Messages views (placeholder)
@login_required
def list_messages_view(request):
    from .models import InternalMessage
    from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
    
    # Buscar mensagens baseadas nas permissões do usuário
    messages_query = InternalMessage.objects.filter(enterprise=request.user.enterprise)
    
    # Se o usuário tem permissão limitada (só vê mensagens das suas unidades)
    if request.user.has_perm('users.view_unit_messages') and not request.user.has_perm('users.view_all_messages'):
        user_units = request.user.units.all()
        if user_units.exists():
            # Mensagens da empresa toda + mensagens específicas das unidades do usuário
            from django.db import models as django_models
            messages_query = messages_query.filter(
                django_models.Q(scope='empresa') | 
                django_models.Q(scope='unidade', unit__in=user_units)
            )
        else:
            # Se não tem unidade, só vê mensagens da empresa
            messages_query = messages_query.filter(scope='empresa')
    
    # Ordenar por data (mais recentes primeiro)
    messages_query = messages_query.order_by('-date')
    
    # Paginação
    paginator = Paginator(messages_query, 10)
    page = request.GET.get('page', 1)

    try:
        internal_messages = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        internal_messages = paginator.page(1)
    
    context = {
        'enterprise': request.user.enterprise,
        'internal_messages': internal_messages
    }
    return render(request, 'enterprises/list_messages.html', context)

@login_required
def edit_message_view(request, message_id):
    from .models import InternalMessage
    from units.models import Unit
    
    # Verificar permissões para editar mensagens
    if not request.user.has_perm('users.change_messages'):
        messages.error(request, 'Você não tem permissão para editar mensagens.')
        return redirect('list_messages')
    
    message = get_object_or_404(InternalMessage, id=message_id, enterprise=request.user.enterprise)
    
    # Se o usuário só pode editar mensagens das suas unidades
    if request.user.has_perm('users.view_unit_messages') and not request.user.has_perm('users.view_all_messages'):
        user_units = request.user.units.all()
        if message.scope == 'unidade' and message.unit not in user_units:
            messages.error(request, 'Você só pode editar mensagens das suas unidades.')
            return redirect('list_messages')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        level = request.POST.get('level', 'info')
        scope = request.POST.get('scope', 'empresa')
        unit_id = request.POST.get('unit_id', '') or request.POST.get('unit', '')
        expires_at = request.POST.get('expires_at', '')
        
        # Validações
        error_found = False
        
        if not title:
            messages.error(request, 'O título é obrigatório.')
            error_found = True
        elif not content:
            messages.error(request, 'O conteúdo é obrigatório.')
            error_found = True
        elif scope == 'unidade' and not unit_id:
            messages.error(request, 'Selecione uma unidade quando o escopo for "Unidade Específica".')
            error_found = True
        elif scope == 'unidade' and unit_id:
            # Verificar se o usuário pode editar para essa unidade
            if not request.user.has_perm('users.view_all_messages'):
                user_units = request.user.units.all()
                if not user_units.filter(id=unit_id).exists():
                    messages.error(request, 'Você só pode editar mensagens para unidades às quais está vinculado.')
                    error_found = True
        elif scope == 'empresa':
            # Verificar se o usuário pode criar/editar mensagens da empresa
            if not request.user.has_perm('users.add_company_messages'):
                messages.error(request, 'Você não tem permissão para editar mensagens da empresa.')
                error_found = True
        
        if not error_found:
            try:
                message.title = title
                message.content = content
                message.level = level
                message.scope = scope
                
                if scope == 'unidade' and unit_id:
                    unit = Unit.objects.get(id=unit_id, enterprise=request.user.enterprise)
                    message.unit = unit
                else:
                    message.unit = None
                
                if expires_at:
                    from datetime import datetime
                    message.expires_at = datetime.strptime(expires_at, '%Y-%m-%d')
                else:
                    message.expires_at = None
                
                message.save()
                messages.success(request, 'Mensagem atualizada com sucesso!')
                return redirect('list_messages')
                
            except Unit.DoesNotExist:
                messages.error(request, 'Unidade selecionada não encontrada.')
            except ValueError:
                messages.error(request, 'Data de expiração inválida.')
    
        # Buscar unidades acessíveis ao usuário  
    if request.user.has_perm('users.view_all_messages'):
        # Usuário pode ver todas as unidades
        units = Unit.objects.filter(enterprise=request.user.enterprise, is_active=True)
        user_units = units
        has_multiple_units = True  # Sempre múltiplas opções para cargos superiores
        single_unit = None
    else:
        # Usuário só pode ver suas próprias unidades
        user_units = request.user.units.filter(is_active=True)
        units = user_units
        has_multiple_units = user_units.count() > 1
        single_unit = user_units.first() if user_units.count() == 1 else None
    
    # Verificar permissões para o template
    can_add_unit_messages = request.user.has_perm('users.add_unit_messages')
    can_add_company_messages = request.user.has_perm('users.add_company_messages')
    
    context = {
        'enterprise': request.user.enterprise,
        'message': message,
        'units': units,
        'user_units': user_units,
        'has_multiple_units': has_multiple_units,
        'single_unit': single_unit,
        'can_add_unit_messages': can_add_unit_messages,
        'can_add_company_messages': can_add_company_messages,
        'form_data': {
            'title': message.title,
            'content': message.content,
            'level': message.level,
            'scope': message.scope,
            'unit': message.unit.id if message.unit else '',
            'expires_at': message.expires_at.strftime('%Y-%m-%d') if message.expires_at else '',
        }
    }
    return render(request, 'enterprises/edit_message.html', context)

@login_required
def new_message_view(request):
    from .models import InternalMessage
    from units.models import Unit
    
    # Verificar permissões baseadas no escopo da mensagem
    can_add_unit_messages = request.user.has_perm('users.add_unit_messages')
    can_add_company_messages = request.user.has_perm('users.add_company_messages')
    
    if not (can_add_unit_messages or can_add_company_messages):
        messages.error(request, 'Você não tem permissão para criar mensagens.')
        return redirect('list_messages')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        level = request.POST.get('level', 'info')
        scope = request.POST.get('scope', 'empresa')
        unit_id = request.POST.get('unit_id', '') or request.POST.get('unit', '')
        expires_at = request.POST.get('expires_at', '')
        
        # Validações
        error_found = False
        
        if not title:
            messages.error(request, 'O título é obrigatório.')
            error_found = True
        elif not content:
            messages.error(request, 'O conteúdo é obrigatório.')
            error_found = True
        elif scope == 'unidade' and not unit_id:
            messages.error(request, 'Selecione uma unidade quando o escopo for "Unidade Específica".')
            error_found = True
        elif scope == 'empresa' and not can_add_company_messages:
            messages.error(request, 'Você não tem permissão para criar mensagens para toda a empresa.')
            error_found = True
        elif scope == 'unidade' and not can_add_unit_messages:
            messages.error(request, 'Você não tem permissão para criar mensagens para unidades.')
            error_found = True
        elif scope == 'unidade' and unit_id:
            # Verificar se o usuário está vinculado à unidade selecionada (exceto para cargos superiores)
            if not request.user.has_perm('users.view_all_messages'):
                user_units = request.user.units.all()
                if not user_units.filter(id=unit_id).exists():
                    messages.error(request, 'Você só pode criar mensagens para unidades às quais está vinculado.')
                    error_found = True
        
        if not error_found:
            try:
                message = InternalMessage(
                    title=title,
                    content=content,
                    level=level,
                    scope=scope,
                    enterprise=request.user.enterprise
                )
                
                if scope == 'unidade':
                    if unit_id:
                        unit = Unit.objects.get(id=unit_id, enterprise=request.user.enterprise)
                        message.unit = unit
                    elif not request.user.has_perm('users.view_all_messages'):
                        # Se o usuário tem apenas uma unidade, usar automaticamente
                        user_units = request.user.units.filter(is_active=True)
                        if user_units.count() == 1:
                            message.unit = user_units.first()
                
                if expires_at:
                    from datetime import datetime
                    message.expires_at = datetime.strptime(expires_at, '%Y-%m-%d')
                
                message.save()
                messages.success(request, 'Mensagem criada com sucesso!')
                return redirect('list_messages')
                
            except Unit.DoesNotExist:
                messages.error(request, 'Unidade selecionada não encontrada.')
            except ValueError:
                messages.error(request, 'Data de expiração inválida.')
    
        # Buscar unidades acessíveis ao usuário
    if request.user.has_perm('users.view_all_messages'):
        # Usuário pode ver todas as unidades
        units = Unit.objects.filter(enterprise=request.user.enterprise, is_active=True)
        user_units = units
        has_multiple_units = True  # Sempre múltiplas opções para cargos superiores
        single_unit = None
    else:
        # Usuário só pode ver suas próprias unidades
        user_units = request.user.units.filter(is_active=True)
        units = user_units
        has_multiple_units = user_units.count() > 1
        single_unit = user_units.first() if user_units.count() == 1 else None
    
    # Dados do formulário para manter em caso de erro
    form_data = {
        'title': request.POST.get('title', '') if request.method == 'POST' else '',
        'content': request.POST.get('content', '') if request.method == 'POST' else '',
        'level': request.POST.get('level', 'info') if request.method == 'POST' else 'info',
        'scope': request.POST.get('scope', 'empresa') if request.method == 'POST' else 'empresa',
        'unit': request.POST.get('unit', '') if request.method == 'POST' else '',
        'expires_at': request.POST.get('expires_at', '') if request.method == 'POST' else '',
    }
    
    context = {
        'enterprise': request.user.enterprise,
        'units': units,
        'user_units': user_units,
        'has_multiple_units': has_multiple_units,
        'single_unit': single_unit,
        'form_data': form_data,
        'can_add_unit_messages': can_add_unit_messages,
        'can_add_company_messages': can_add_company_messages
    }
    return render(request, 'enterprises/new_message.html', context)

# View de teste para demonstrar redirecionamento
@login_required
def test_redirect_view(request):
    """View para testar redirecionamento de subdomínios"""
    user = request.user
    current_enterprise = getattr(request, 'current_enterprise', None)
    
    context = {
        'user': user,
        'user_enterprise': user.enterprise,
        'current_enterprise': current_enterprise,
        'should_redirect': current_enterprise and current_enterprise != user.enterprise,
        'correct_url': user.enterprise.get_absolute_url() if user.enterprise else None,
        'current_host': request.get_host(),
        'is_subdomain_access': current_enterprise is not None,
    }
    
    # Se o usuário está na empresa errada, simular redirecionamento
    if current_enterprise and user.enterprise and current_enterprise != user.enterprise:
        messages.warning(
            request, 
            f"Você foi redirecionado de {current_enterprise.name} para {user.enterprise.name} "
            f"porque pertence à empresa {user.enterprise.name}."
        )
        return redirect(user.enterprise.get_absolute_url())
    
    return render(request, 'enterprises/test_redirect.html', context)