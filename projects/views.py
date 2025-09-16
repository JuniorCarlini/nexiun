from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render
from enterprises.models import Client
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Project, Enterprise, User, CreditLine, Bank, ProjectDocument, ProjectHistory, PROJECT_STATUS_CHOICES, ACTIVITY_CHOICES, SIZE_CHOICES, TYPE_CHOICES
from core.mixins import get_selected_unit_from_request, is_all_units_selected_from_request, get_accessible_units_from_request

# Cria um novo projeto
@login_required
def create_project_view(request):
    # Verificar se o usuário tem permissão para criar projetos
    if not request.user.has_perm('users.add_projects'):
        messages.error(request, "Você não tem permissão para criar projetos.")
        return redirect('home')

    # Verificar se está tentando criar com "Todas as unidades" selecionado
    is_all_units_selected = is_all_units_selected_from_request(request)
    if request.method == "POST":
        if is_all_units_selected:
            messages.error(request, 'Para criar projetos, você deve estar em uma unidade específica. Altere sua sessão antes de continuar.')
            return redirect('create_project')
            
        try:
            # Processar dados do formulário
            value = request.POST.get('value', '')
            value = value.replace('.', '').replace(',', '.')

            # Criar novo projeto
            project = Project(
                client_id=request.POST.get('client'),
                bank_id=request.POST.get('bank'),
                credit_line_id=request.POST.get('credit_line'),
                activity=request.POST.get('activity'),
                size=request.POST.get('size'),
                land_size=request.POST.get('land_size'),
                project_deadline=request.POST.get('project_deadline'),
                installments=request.POST.get('installments'),
                fees=request.POST.get('fees'),
                payment_grace=request.POST.get('payment_grace'),
                percentage_astec=request.POST.get('percentage_astec'),
                description=request.POST.get('description'),
                next_phase_deadline=request.POST.get('next_phase_deadline'),
                enterprise=request.user.enterprise
            )
            
            # Verificar se foi selecionado um projetista responsável
            project_designer_id = request.POST.get('project_designer')
            if project_designer_id:
                try:
                    project_designer = User.objects.get(
                        id=project_designer_id, 
                        enterprise=request.user.enterprise,
                        roles__code='projetista'
                    )
                    project.project_designer = project_designer
                    # Mantém status "Em Acolhimento" mesmo com projetista selecionado
                    # project.status = 'AC'  # Não precisa definir pois já é o padrão
                except User.DoesNotExist:
                    messages.warning(request, "Projetista selecionado não encontrado.")
            # Status padrão sempre 'AC' (Em Acolhimento)

            if value:
                project.value = Decimal(value)
            
            # Associar projeto à unidade da sessão atual
            selected_unit_id = request.POST.get('unit_id')
            selected_unit = get_selected_unit_from_request(request)
            accessible_units = get_accessible_units_from_request(request)
            
            if selected_unit_id:
                # Unidade específica selecionada no formulário
                if request.user.has_perm('users.view_all_units'):
                    # Usuário com view_all_units pode selecionar qualquer unidade da empresa
                    selected_unit_obj = request.user.enterprise.units.filter(id=selected_unit_id, is_active=True).first()
                    if selected_unit_obj:
                        project.unit = selected_unit_obj
                    else:
                        messages.error(request, 'Unidade selecionada inválida.')
                        return redirect('create_project')
                else:
                    # Usuário normal: só pode selecionar suas unidades vinculadas
                    if accessible_units.filter(id=selected_unit_id).exists():
                        project.unit_id = selected_unit_id
                    else:
                        messages.error(request, 'Você não tem acesso à unidade selecionada.')
                        return redirect('create_project')
            elif selected_unit:
                # Usar unidade da sessão
                project.unit = selected_unit
            else:
                messages.error(request, 'Erro: Nenhuma unidade disponível para o projeto.')
                return redirect('create_project')
            
            project.save()

            # Processar documentos
            files = request.FILES.getlist('documents[]')
            for file in files:
                if file.size > 20 * 1024 * 1024:  # 20MB limit
                    messages.error(request, f"O arquivo {file.name} excede o limite de 20MB")
                    continue
                    
                file_type = file.content_type
                if file_type not in ['application/pdf', 'image/jpeg', 'image/png']:
                    messages.error(request, f"O arquivo {file.name} não é um tipo permitido (PDF, JPG, PNG)")
                    continue

                ProjectDocument.objects.create(
                    project=project,
                    file=file,
                    file_name=file.name,
                    file_type=file_type,
                    file_size=file.size
                )

            # Mensagem de sucesso personalizada baseada na atribuição
            if project.project_designer:
                messages.success(request, f"Projeto criado e atribuído ao projetista {project.project_designer.name}! Status: Em Acolhimento.")
            else:
                messages.success(request, "Projeto criado com sucesso! Status: Em Acolhimento - disponível na esteira de projetos.")
            
            return redirect('project_details', project_id=project.id)

        except Exception as e:
            messages.error(request, f"Erro ao criar o projeto: {str(e)}")
            return redirect('create_project')

    # Obter informações da sessão e unidades
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Verificar se usuário tem acesso a unidades
    if not request.user.has_perm('users.view_all_units'):
        if not accessible_units.exists():
            messages.error(request, "Você precisa estar vinculado a pelo menos uma unidade para criar projetos.")
            return redirect('projects_list')

    # Filtrar clientes baseado na unidade selecionada na sessão
    if is_all_units_selected:
        # Se "Todas as unidades" está selecionado, mostrar todos os clientes baseado na permissão
        if request.user.has_perm('users.view_all_clients'):
            # Usuários que podem ver todos os clientes da empresa
            clients = Client.objects.filter(enterprise=request.user.enterprise)
        else:
            # Usuários que só podem ver clientes das suas unidades
            clients = Client.objects.filter(
                enterprise=request.user.enterprise,
                units__in=accessible_units
            )
    elif selected_unit:
        # Se uma unidade específica está selecionada, mostrar apenas clientes dessa unidade
        clients = Client.objects.filter(
            enterprise=request.user.enterprise,
            units=selected_unit
        )
    else:
        # Se não há unidade selecionada, usar as unidades acessíveis
        if request.user.has_perm('users.view_all_clients'):
            clients = Client.objects.filter(enterprise=request.user.enterprise)
        else:
            clients = Client.objects.filter(
                enterprise=request.user.enterprise,
                units__in=accessible_units
            )

    credit_lines = CreditLine.objects.filter(enterprise=request.user.enterprise)
    banks = Bank.objects.filter(enterprise=request.user.enterprise)
    
    # Buscar projetistas disponíveis da mesma empresa
    projetistas = User.objects.filter(
        enterprise=request.user.enterprise,
        roles__code='projetista',
        is_active=True
    ).distinct()

    return render(request, 'projects/create_project.html', {
        'clients': clients,
        'credit_lines': credit_lines,
        'banks': banks,
        'projetistas': projetistas,
        'size_choices': SIZE_CHOICES,
        'activity_choices': ACTIVITY_CHOICES,
        'is_completed': False,
        'project': None,
        'enterprise': request.user.enterprise,
        'user_units': accessible_units,
        'accessible_units': accessible_units,
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
        'can_view_all_units': request.user.has_perm('users.view_all_units'),
        'has_multiple_units': accessible_units.count() > 1 or request.user.has_perm('users.view_all_units'),
        'single_unit': accessible_units.first() if accessible_units.count() == 1 and not request.user.has_perm('users.view_all_units') else None
    })

# Adiciona um novo banco
@login_required
def add_bank_view(request):
    # Verificar se o usuário tem permissão master para gerenciar bancos
    if not request.user.has_perm('users.manage_banks_master'):
        messages.error(request, 'Você não tem permissão para gerenciar bancos.')
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        # Validar campos obrigatórios
        if not name:
            messages.error(request, 'O nome do banco é obrigatório!')
            return redirect('bank_add')
        
        # Criar o banco usando a empresa do usuário
        Bank.objects.create(
            name=name,
            description=description,
            enterprise=request.user.enterprise  # Usa a empresa do usuário logado
        )
        
        messages.success(request, 'Banco cadastrado com sucesso!')
        return redirect('banks_list')
    
    return render(request, 'projects/add_bank.html')

# Editar o banco
@login_required
def bank_edit_view(request, bank_id):
    # Verificar se o usuário tem permissão master para gerenciar bancos
    if not request.user.has_perm('users.manage_banks_master'):
        messages.error(request, 'Você não tem permissão para gerenciar bancos.')
        return redirect('home')
    
    bank = get_object_or_404(Bank, id=bank_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if not name:
            messages.error(request, 'O nome do banco é obrigatório!')
            return redirect('bank_edit', bank_id=bank_id)
        
        bank.name = name
        bank.description = description
        bank.save()
        
        messages.success(request, 'Banco atualizado com sucesso!')
        return redirect('banks_list')
    
    return render(request, 'projects/edit_bank.html', {
        'bank': bank
    })

# Lista os Bancos
@login_required
def banks_list_view(request):
    # Verificar se o usuário tem permissão para acessar a página
    if not request.user.has_perm('users.view_banks'):
        messages.error(request, 'Você não tem permissão para visualizar bancos.')
        return redirect('home')
    
    # Configurar a paginação
    page = request.GET.get('page', 1)
    banks = Bank.objects.filter(enterprise=request.user.enterprise).order_by('-is_active', 'name')  # Ativos primeiro, depois por nome
    paginator = Paginator(banks, 10)  # 10 bancos por página
    
    try:
        banks_page = paginator.page(page)
    except PageNotAnInteger:
        banks_page = paginator.page(1)
    except EmptyPage:
        banks_page = paginator.page(paginator.num_pages)
    
    return render(request, 'projects/list_banks.html', {
        'banks': banks_page,  # Passar os bancos paginados
    })

# Ativa/Desativa um banco (ao invés de excluir)
@login_required
def toggle_bank_status_view(request, bank_id):
    # Verificar se o usuário tem permissão
    if not request.user.has_perm('users.change_banks'):
        messages.error(request, 'Você não tem permissão para alterar bancos.')
        return redirect('banks_list')
    
    # Garantir que o usuário só pode alterar bancos da sua própria empresa
    bank = get_object_or_404(Bank, id=bank_id, enterprise=request.user.enterprise)
    
    if request.method == 'POST':
        # Alterna o status do banco
        bank.is_active = not bank.is_active
        bank.save()
        
        status_text = "ativado" if bank.is_active else "desativado"
        messages.success(request, f'Banco "{bank.name}" foi {status_text} com sucesso!')
    
    return redirect('banks_list')

# Adiciona uma nova Linha de Crédito
@login_required
def add_credit_line_view(request):
    # Verificar se o usuário tem permissão master para gerenciar linhas de crédito
    if not request.user.has_perm('users.manage_credit_lines_master'):
        messages.error(request, 'Você não tem permissão para gerenciar linhas de crédito.')
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        type_credit = request.POST.get('type_credit')
        
        # Validar campos obrigatórios
        if not name:
            messages.error(request, 'O nome da linha de crédito é obrigatório!')
            return redirect('credit_line_add')
        
        # Criar a linha de crédito usando a empresa do usuário
        CreditLine.objects.create(
            name=name,
            description=description,
            type_credit=type_credit,
            enterprise=request.user.enterprise
        )
        
        messages.success(request, 'Linha de crédito cadastrada com sucesso!')
        return redirect('credit_line_list')
    
    context = {
        'type_choices': TYPE_CHOICES
    }

    return render(request, 'projects/add_credit_line.html', context)

# Editar a Linha de Crédito
@login_required
def credit_line_edit_view(request, credit_line_id):
    # Verificar se o usuário tem permissão master para gerenciar linhas de crédito
    if not request.user.has_perm('users.manage_credit_lines_master'):
        messages.error(request, 'Você não tem permissão para gerenciar linhas de crédito.')
        return redirect('home')
    
    credit_line = get_object_or_404(CreditLine, id=credit_line_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        type_credit = request.POST.get('type_credit')
        description = request.POST.get('description')
        
        if not name:
            messages.error(request, 'O nome da linha de crédito é obrigatório!')
            return redirect('credit_line_edit', credit_line_id=credit_line_id)
        
        credit_line.name = name
        credit_line.description = description
        credit_line.type_credit = type_credit
        credit_line.save()
        
        messages.success(request, 'Linha de crédito atualizada com sucesso!')
        return redirect('credit_line_list')
    
    context = {
        'credit_line': credit_line,
        'type_choices': TYPE_CHOICES
    }

    return render(request, 'projects/edit_credit_line.html', context)

# Lista as Linhas de Crédito
@login_required
def credit_lines_list_view(request):
    # Verificar se o usuário tem permissão para acessar a página
    if not request.user.has_perm('users.view_credit_lines'):
        messages.error(request, 'Você não tem permissão para visualizar linhas de crédito.')
        return redirect('home')

    # Configurar a paginação
    page = request.GET.get('page', 1)
    credit_lines = CreditLine.objects.filter(enterprise=request.user.enterprise).order_by('-is_active', 'name')  # Ativas primeiro, depois por nome
    paginator = Paginator(credit_lines, 10)  # 10 linhas de crédito por página
    
    try:
        credit_lines_page = paginator.page(page)
    except PageNotAnInteger:
        credit_lines_page = paginator.page(1)
    except EmptyPage:
        credit_lines_page = paginator.page(paginator.num_pages)
    
    return render(request, 'projects/list_credit_lines.html', {  # Corrigido o nome do template
        'credit_lines': credit_lines_page,
    })

# Ativa/Desativa uma linha de crédito (ao invés de excluir)
@login_required
def toggle_credit_line_status_view(request, credit_line_id):
    # Verificar se o usuário tem permissão
    if not request.user.has_perm('users.change_credit_lines'):
        messages.error(request, 'Você não tem permissão para alterar linhas de crédito.')
        return redirect('credit_line_list')
    
    # Garantir que o usuário só pode alterar linhas de crédito da sua própria empresa
    credit_line = get_object_or_404(CreditLine, id=credit_line_id, enterprise=request.user.enterprise)
    
    if request.method == 'POST':
        # Alterna o status da linha de crédito
        credit_line.is_active = not credit_line.is_active
        credit_line.save()
        
        status_text = "ativada" if credit_line.is_active else "desativada"
        messages.success(request, f'Linha de crédito "{credit_line.name}" foi {status_text} com sucesso!')
    
    return redirect('credit_line_list')

# Lista de projetos
@login_required
def projects_list_view(request):
    from core.mixins import get_selected_unit_from_request, is_all_units_selected_from_request
    
    if not request.user.has_perm('users.view_projects'):
        messages.error(request, "Você não tem permissão para visualizar projetos.")
        return redirect('home')
        
    status_filter = request.GET.get('status', None)

    projects = Project.objects.select_related('client')
    
    # Verificar se está selecionado "Todas as unidades"
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    if is_all_units_selected:
        # Quando "Todas as unidades" está selecionado
        if request.user.has_perm('users.view_all_projects'):
            # Pode ver todos os projetos da empresa
            projects = projects.filter(unit__enterprise=request.user.enterprise)
        else:
            # Aplicar lógica de permissão baseada no acesso do usuário
            if request.user.has_perm('users.view_own_projects') and not request.user.has_perm('users.view_unit_projects'):
                # Ver apenas próprios projetos
                projects = projects.filter(project_designer=request.user)
            elif request.user.has_perm('users.view_unit_projects'):
                # Ver projetos das unidades que tem acesso
                if request.user.has_perm('users.view_all_units'):
                    # Tem acesso a todas as unidades da empresa
                    projects = projects.filter(unit__enterprise=request.user.enterprise)
                else:
                    # Ver projetos das suas unidades vinculadas
                    user_units = request.user.units.all()
                    projects = projects.filter(unit__in=user_units)
    else:
        # Lógica normal baseada na unidade selecionada
        selected_unit = get_selected_unit_from_request(request)
        
        if selected_unit:
            # Filtrar pela unidade específica selecionada
            if request.user.has_perm('users.view_all_projects'):
                # Pode ver todos os projetos da unidade
                projects = projects.filter(unit=selected_unit)
            elif request.user.has_perm('users.view_unit_projects'):
                # Pode ver projetos da unidade se tiver acesso a ela
                if request.user.has_perm('users.view_all_units') or request.user.units.filter(id=selected_unit.id).exists():
                    projects = projects.filter(unit=selected_unit)
                else:
                    # Não tem acesso à unidade selecionada
                    projects = projects.none()
            elif request.user.has_perm('users.view_own_projects'):
                # Ver apenas próprios projetos na unidade selecionada
                projects = projects.filter(project_designer=request.user, unit=selected_unit)
        else:
            # Nenhuma unidade selecionada - aplicar lógica de permissão padrão
            if request.user.has_perm('users.view_own_projects') and not request.user.has_perm('users.view_unit_projects'):
                # Ver apenas próprios projetos
                projects = projects.filter(project_designer=request.user)
            elif request.user.has_perm('users.view_unit_projects') and not request.user.has_perm('users.view_all_projects'):
                # Ver projetos das unidades
                user_units = request.user.units.all()
                projects = projects.filter(unit__in=user_units)
    
    # Calcular contagem de projetos por status de forma eficiente ANTES do filtro por status
    from django.db.models import Count, Case, When, IntegerField
    
    # Contar todos os status em uma única query usando agregação
    status_counts = projects.aggregate(
        AC=Count(Case(When(status='AC', then=1), output_field=IntegerField())),
        PE=Count(Case(When(status='PE', then=1), output_field=IntegerField())),
        AN=Count(Case(When(status='AN', then=1), output_field=IntegerField())),
        AP=Count(Case(When(status='AP', then=1), output_field=IntegerField())),
        AF=Count(Case(When(status='AF', then=1), output_field=IntegerField())),
        FM=Count(Case(When(status='FM', then=1), output_field=IntegerField())),
        LB=Count(Case(When(status='LB', then=1), output_field=IntegerField())),
        RC=Count(Case(When(status='RC', then=1), output_field=IntegerField())),
    )
        
    if status_filter:
        projects = projects.filter(status=status_filter)

    for project in projects:
        if project.next_phase_deadline:
            dias_restantes = (project.next_phase_deadline - date.today()).days
            if dias_restantes < 0:
                project.deadline_status = 'red'
            elif dias_restantes <= 1:
                project.deadline_status = 'yellow' 
            else:
                project.deadline_status = 'green'
        else:
            project.deadline_status = 'gray'

    current_status_description = next(
        (desc for code, desc in PROJECT_STATUS_CHOICES if code == status_filter),
        None
    )

    paginator = Paginator(projects, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'projects': page_obj,
        'current_status': current_status_description if status_filter else ' ',
        'project_status_choices': PROJECT_STATUS_CHOICES,
        'status_counts': status_counts,
        'is_all_units_selected': is_all_units_selected,
        'selected_unit': get_selected_unit_from_request(request) if not is_all_units_selected else None
    }

    return render(request, 'projects/list_projects.html', context)
    
# Esteira de Pagamentos
@login_required
def conveyor_payments_view(request):
    # Verificar se o usuário tem permissão para acessar pagamentos
    if not request.user.has_perm('users.view_project_payments'):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('home')
    
    # Obter informações da sessão e unidades
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Filtrar projetos que estão em LB (Liberado)
    projects = Project.objects.filter(
        status='LB',
    )
    
    # Aplicar filtro de unidade baseado na sessão
    if is_all_units_selected:
        # Se "Todas as unidades" está selecionado
        if request.user.has_perm('users.view_all_projects') or request.user.has_perm('users.view_project_payments'):
            # Pode ver todos os projetos da empresa
            projects = projects.filter(unit__enterprise=request.user.enterprise)
        else:
            # Aplicar lógica de permissão baseada no acesso do usuário
            if request.user.has_perm('users.view_unit_projects'):
                # Ver projetos das unidades que tem acesso
                if request.user.has_perm('users.view_all_units'):
                    # Tem acesso a todas as unidades da empresa
                    projects = projects.filter(unit__enterprise=request.user.enterprise)
                else:
                    # Ver projetos das suas unidades vinculadas
                    projects = projects.filter(unit__in=accessible_units)
            else:
                # Ver apenas próprios projetos
                projects = projects.filter(project_designer=request.user)
    elif selected_unit:
        # Se uma unidade específica está selecionada
        if request.user.has_perm('users.view_all_projects') or request.user.has_perm('users.view_project_payments'):
            # Pode ver todos os projetos da unidade
            projects = projects.filter(unit=selected_unit)
        elif request.user.has_perm('users.view_unit_projects'):
            # Pode ver projetos da unidade se tiver acesso a ela
            if request.user.has_perm('users.view_all_units') or request.user.units.filter(id=selected_unit.id).exists():
                projects = projects.filter(unit=selected_unit)
            else:
                # Não tem acesso à unidade selecionada
                projects = projects.none()
        else:
            # Ver apenas próprios projetos na unidade selecionada
            projects = projects.filter(project_designer=request.user, unit=selected_unit)
    else:
        # Nenhuma unidade selecionada - aplicar lógica de permissão padrão
        if request.user.has_perm('users.view_project_payments'):
            # Usuários com permissão de pagamentos podem ver todos os projetos da empresa
            projects = projects.filter(unit__enterprise=request.user.enterprise)
        elif request.user.has_perm('users.view_unit_projects') and not request.user.has_perm('users.view_all_projects'):
            # Ver projetos das unidades acessíveis
            projects = projects.filter(unit__in=accessible_units)
        elif not request.user.has_perm('users.view_unit_projects'):
            # Ver apenas próprios projetos
            projects = projects.filter(project_designer=request.user)
    
    # Paginação
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'projects/conveyor_payments.html', {
        'projects': page_obj,
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
        'accessible_units': accessible_units,
    })

# Esteira de Confirmacão de Pagamentos
@login_required
def conveyor_confirm_payments_view(request):
    # Verifica se o usuário tem permissão para confirmar pagamentos
    if not request.user.has_perm('users.change_project_payments'):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('home')
    
    # Obter informações da sessão e unidades
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Filtrar projetos em RC e não finalizados
    projects = Project.objects.filter(
        status='RC',
        project_finalized=False
    ).order_by('-id')  # Ordenar por data de criação
    
    # Aplicar filtro de unidade baseado na sessão
    if is_all_units_selected:
        # Se "Todas as unidades" está selecionado
        if request.user.has_perm('users.view_all_projects') or request.user.has_perm('users.change_project_payments'):
            # Pode ver todos os projetos da empresa
            projects = projects.filter(unit__enterprise=request.user.enterprise)
        else:
            # Aplicar lógica de permissão baseada no acesso do usuário
            if request.user.has_perm('users.view_unit_projects'):
                # Ver projetos das unidades que tem acesso
                if request.user.has_perm('users.view_all_units'):
                    # Tem acesso a todas as unidades da empresa
                    projects = projects.filter(unit__enterprise=request.user.enterprise)
                else:
                    # Ver projetos das suas unidades vinculadas
                    projects = projects.filter(unit__in=accessible_units)
            else:
                # Ver apenas próprios projetos
                projects = projects.filter(project_designer=request.user)
    elif selected_unit:
        # Se uma unidade específica está selecionada
        if request.user.has_perm('users.view_all_projects') or request.user.has_perm('users.change_project_payments'):
            # Pode ver todos os projetos da unidade
            projects = projects.filter(unit=selected_unit)
        elif request.user.has_perm('users.view_unit_projects'):
            # Pode ver projetos da unidade se tiver acesso a ela
            if request.user.has_perm('users.view_all_units') or request.user.units.filter(id=selected_unit.id).exists():
                projects = projects.filter(unit=selected_unit)
            else:
                # Não tem acesso à unidade selecionada
                projects = projects.none()
        else:
            # Ver apenas próprios projetos na unidade selecionada
            projects = projects.filter(project_designer=request.user, unit=selected_unit)
    else:
        # Nenhuma unidade selecionada - aplicar lógica de permissão padrão
        if request.user.has_perm('users.change_project_payments'):
            # Usuários com permissão de alteração de pagamentos podem ver todos os projetos da empresa
            projects = projects.filter(unit__enterprise=request.user.enterprise)
        elif request.user.has_perm('users.view_unit_projects') and not request.user.has_perm('users.view_all_projects'):
            # Ver projetos das unidades acessíveis
            projects = projects.filter(unit__in=accessible_units)
        elif not request.user.has_perm('users.view_unit_projects'):
            # Ver apenas próprios projetos
            projects = projects.filter(project_designer=request.user)
    
    # Paginação
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'projects': page_obj,
        'title': 'Esteira de Confirmação de Pagamentos',
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
        'accessible_units': accessible_units,
    }
    
    return render(request, 'projects/conveyor_confirm_payments.html', context)

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Project, User

# Atribuir gerente ao projeto
@login_required
def assign_manager_view(request, project_id):
    if request.method == "POST":
        project = get_object_or_404(Project, id=project_id)
        manager_id = request.POST.get("manager")
        responsible_id = request.POST.get("responsible")
        manager = get_object_or_404(User, id=manager_id)
        responsible = get_object_or_404(User, id=responsible_id)

        project.project_manager = manager
        project.project_designer = responsible
        project.save()

        return redirect("conveyor_projects_view") 

# Esteira de projetos
@login_required
def conveyor_projects_view(request):
    # Verificar se o usuário tem permissão para acessar a página
    if not request.user.has_perm('users.view_projects'):
        messages.error(request, "Você não tem permissão para acessar a esteira de projetos.")
        return redirect('home')
    
    # Obter informações da sessão e unidades
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Filtrar projetos que estão em AC e não possuem Projetista
    projects = Project.objects.filter(
        status='AC',
        project_designer__isnull=True
    )
    
    # Aplicar filtro de unidade baseado na sessão
    if is_all_units_selected:
        # Se "Todas as unidades" está selecionado
        if request.user.has_perm('users.view_all_projects'):
            # Pode ver todos os projetos da empresa
            projects = projects.filter(unit__enterprise=request.user.enterprise)
        else:
            # Aplicar lógica de permissão baseada no acesso do usuário
            if request.user.has_perm('users.view_unit_projects'):
                # Ver projetos das unidades que tem acesso
                if request.user.has_perm('users.view_all_units'):
                    # Tem acesso a todas as unidades da empresa
                    projects = projects.filter(unit__enterprise=request.user.enterprise)
                else:
                    # Ver projetos das suas unidades vinculadas
                    projects = projects.filter(unit__in=accessible_units)
            else:
                # Como é esteira de projetos sem projetista, não aplicar filtro adicional de usuário
                # Já está filtrando por project_designer__isnull=True
                pass
    elif selected_unit:
        # Se uma unidade específica está selecionada
        if request.user.has_perm('users.view_all_projects'):
            # Pode ver todos os projetos da unidade
            projects = projects.filter(unit=selected_unit)
        elif request.user.has_perm('users.view_unit_projects'):
            # Pode ver projetos da unidade se tiver acesso a ela
            if request.user.has_perm('users.view_all_units') or request.user.units.filter(id=selected_unit.id).exists():
                projects = projects.filter(unit=selected_unit)
            else:
                # Não tem acesso à unidade selecionada
                projects = projects.none()
        else:
            # Como é esteira de projetos sem projetista, aplicar filtro de unidade apenas
            projects = projects.filter(unit=selected_unit)
    else:
        # Nenhuma unidade selecionada - aplicar lógica de permissão padrão
        if request.user.has_perm('users.view_unit_projects') and not request.user.has_perm('users.view_all_projects'):
            # Ver projetos das unidades acessíveis
            projects = projects.filter(unit__in=accessible_units)
        elif not request.user.has_perm('users.view_unit_projects'):
            # Como é esteira de projetos sem projetista, não aplicar filtro adicional de usuário
            # Já está filtrando por project_designer__isnull=True
            pass
    
    # Paginação
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'projects/conveyor_projects.html', {
        'projects': page_obj,
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
        'accessible_units': accessible_units,
    })

# Tela de detalhes do projeto na esteira
@login_required
def conveyor_project_details_view(request, project_id):
    if not request.user.has_perm('users.view_projects'):
        messages.error(request, "Você não tem permissão para visualizar projetos.")
        return redirect('home')

    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        if request.user.has_perm('users.change_projects'):  # Verifica se pode alterar projetos
            manager_id = request.POST.get("manager")
            manager = get_object_or_404(User, id=manager_id)

            # Verificar se o manager tem o cargo apropriado e está na mesma unidade do projeto
            if manager.roles.filter(code__in=['gerente', 'coordenador', 'socio_unidade', 'franqueado'], is_active=True).exists():
                if manager.units.filter(id=project.unit.id).exists():
                    project.project_manager = manager
                    project.project_designer = request.user  # Adiciona o usuário logado como projetista
                    project.save()
                    
                    # Mensagem personalizada baseada no cargo
                    cargo = "franqueado" if manager.roles.filter(code__in=['socio_unidade', 'franqueado']).exists() else "gerente"
                    messages.success(request, f'{cargo.title()} {manager.name} atribuído com sucesso e você foi definido como projetista do projeto.')
                    return redirect('conveyor_projects')
                else:
                    messages.error(request, 'O usuário selecionado não pertence à mesma unidade do projeto.')
            else:
                messages.error(request, 'O usuário selecionado não tem cargo de gerente ou franqueado.')
        else:
            messages.error(request, 'Você não tem permissão para atribuir um gerente ou ser definido como projetista do projeto.')

    manager = project.project_manager
    partner = User.objects.filter(units=project.unit, roles__code__in=['socio_unidade', 'franqueado'], is_active=True).first()
    # Filtrar apenas gerentes, coordenadores e franqueados da mesma unidade do projeto
    managers_queryset = User.objects.filter(
        units=project.unit,
        roles__code__in=['gerente', 'coordenador', 'socio_unidade', 'franqueado'], 
        is_active=True
    ).distinct()
    
    # Criar lista com informações de cargo para o template
    managers = []
    for user in managers_queryset:
        cargo = "Franqueado" if user.roles.filter(code__in=['socio_unidade', 'franqueado']).exists() else "Gerente"
        managers.append({
            'id': user.id,
            'name': user.name,
            'profile_image': user.profile_image,
            'cargo': cargo
        })
    credit_lines = CreditLine.objects.filter(enterprise=project.enterprise)
    banks = Bank.objects.filter(enterprise=project.enterprise)
    project_documents = ProjectDocument.objects.filter(project=project)

    return render(request, 'projects/conveyor_project_details.html', {
        'project': project,
        'manager': manager,
        'partner': partner,
        'managers': managers,
        'credit_lines': credit_lines,
        'banks': banks,
        'size_choices': SIZE_CHOICES,
        'activity_choices': ACTIVITY_CHOICES,
        'project_documents': project_documents,
    })

# TODO: FIltrar acesso dos projetistas apenas aos projetos que eles fazem parte, e mostre somente os ultimos 30 RC

# Tela de detalhes do projeto
@login_required
def project_details_view(request, project_id):
    if not request.user.has_perm('users.view_projects'):
        messages.error(request, "Você não tem permissão para visualizar projetos.")
        return redirect('home')

    project = get_object_or_404(Project, id=project_id)

    # Verificar se o usuário pode ver apenas seus próprios projetos
    if request.user.has_perm('users.view_own_projects') and not request.user.has_perm('users.view_unit_projects'):
        if project.project_designer != request.user:
            messages.error(request, "Você não tem permissão para acessar este projeto.")
            return redirect('home')

    completed_statuses = ['PE', 'AN', 'AP', 'AF', 'FM', 'LB', 'RC']
    is_completed = project.status in completed_statuses

    if request.method == "POST":
        if "previous_phase" in request.POST:
            status_order = dict((status, index) for index, (status, _) in enumerate(PROJECT_STATUS_CHOICES))
            current_index = status_order[project.status]
            
            if current_index > 0:
                project.status = PROJECT_STATUS_CHOICES[current_index - 1][0]
                project.save()
                messages.success(request, "Projeto retornou para fase anterior.")
            else:
                messages.error(request, "Projeto já está na primeira fase.")
            
            return redirect('project_details', project_id=project_id)
            
        elif "next_phase" in request.POST:
            status_order = dict((status, index) for index, (status, _) in enumerate(PROJECT_STATUS_CHOICES))
            current_index = status_order[project.status]
            next_status = PROJECT_STATUS_CHOICES[current_index + 1][0] if current_index < len(PROJECT_STATUS_CHOICES) - 1 else None
            
            # Verificar se está tentando mover para a fase "Liberado" (LB)
            is_going_to_release_phase = next_status == 'LB'
            is_going_to_last_phase = current_index == len(PROJECT_STATUS_CHOICES) - 2
            
            # Verificar permissões específicas
            if is_going_to_release_phase:
                # Para mover para "Liberado", deve ter permissão e ser da mesma unidade ou ser projetista do projeto
                has_release_permission = request.user.has_perm('users.change_project_release')
                is_project_designer = project.project_designer == request.user
                is_same_unit = request.user.units.filter(id=project.unit.id).exists()
                
                if not has_release_permission:
                    messages.error(request, "Você não tem permissão para liberar projetos.")
                    return redirect('project_details', project_id=project_id)
                
                if not is_project_designer and not is_same_unit:
                    messages.error(request, "Você só pode liberar projetos da sua unidade ou projetos que você é o projetista.")
                    return redirect('project_details', project_id=project_id)
                    
            elif is_going_to_last_phase:
                # Para mover para "Receita" (última fase), verificar permissão específica
                has_revenue_permission = request.user.has_perm('users.change_project_to_revenue')
                if not has_revenue_permission:
                    messages.error(request, "Você não tem permissão para mover o projeto para a fase Receita.")
                    return redirect('project_details', project_id=project_id)
            
            if current_index < len(PROJECT_STATUS_CHOICES) - 1:
                project.status = next_status
                project.save()
                messages.success(request, "Projeto avançou para próxima fase.")
            else:
                messages.error(request, "Projeto já está na última fase.")
                
            return redirect('project_details', project_id=project_id)

        elif "delete_document" in request.POST:
            try:
                document_id = request.POST.get("document_id")
                if not document_id:
                    messages.error(request, "ID do documento não fornecido")
                    return redirect('project_details', project_id=project_id)
                    
                document = ProjectDocument.objects.filter(
                    id=document_id,
                    project_id=project_id
                ).first()
                
                if not document:
                    messages.error(request, "Documento não encontrado")
                    return redirect('project_details', project_id=project_id)
                    
                file_name = document.file_name
                document.delete()
                messages.success(request, f"Documento '{file_name}' excluído com sucesso!")
                
            except Exception as e:
                messages.error(request, f"Erro ao excluir documento: {str(e)}")
                
            return redirect('project_details', project_id=project_id)

        elif "action" in request.POST:
            if request.POST["action"] == "save":
                try:
                    files = request.FILES.getlist('documents[]')
                    for file in files:
                        if file.size > 20 * 1024 * 1024:
                            messages.error(request, f"O arquivo {file.name} excede o limite de 20MB")
                            continue
                            
                        file_type = file.content_type
                        if file_type not in ['application/pdf', 'image/jpeg', 'image/png']:
                            messages.error(request, f"O arquivo {file.name} não é um tipo permitido (PDF, JPG, PNG)")
                            continue

                        ProjectDocument.objects.create(
                            project=project,
                            file=file,
                            file_name=file.name,
                            file_type=file_type,
                            file_size=file.size
                        )

                    value = request.POST.get('value', '')
                    value = value.replace('.', '').replace(',', '.')
                    
                    consortium_value = request.POST.get('consortium_value', '')
                    if consortium_value:
                        consortium_value = consortium_value.replace('.', '').replace(',', '.')
                    
                    project.bank_id = request.POST.get('bank')
                    project.credit_line_id = request.POST.get('credit_line')
                    project.activity = request.POST.get('activity')
                    project.size = request.POST.get('size')
                    project.land_size = request.POST.get('land_size')
                    project.project_deadline = request.POST.get('project_deadline')
                    project.installments = request.POST.get('installments')
                    project.fees = request.POST.get('fees')
                    project.payment_grace = request.POST.get('payment_grace')
                    project.percentage_astec = request.POST.get('percentage_astec')
                    project.description = request.POST.get('description')
                    project.next_phase_deadline = request.POST.get('next_phase_deadline')
                    
                    if value:
                        project.value = Decimal(value)
                        
                    if consortium_value:
                        project.consortium_value = Decimal(consortium_value)

                    project.save()
                    
                    if files:
                        messages.success(request, "Projeto atualizado e documentos enviados com sucesso!")
                    else:
                        messages.success(request, "Projeto atualizado com sucesso!")
                        
                except Exception as e:
                    messages.error(request, f"Erro ao atualizar o projeto: {str(e)}")
                    
            elif request.POST["action"] == "complete_project":
                # Verificar se o usuário tem permissão para concluir projetos
                if not request.user.has_perm('users.complete_project'):
                    messages.error(request, "Você não tem permissão para concluir projetos.")
                    return redirect('project_details', project_id=project_id)
                
                try:
                    if project.status == 'RC':
                        project.project_finalized = True
                        project.save()
                        messages.success(request, "Projeto concluído com sucesso!")
                    else:
                        messages.error(request, "O projeto precisa estar na fase Receita para ser concluído.")
                except Exception as e:
                    messages.error(request, f"Erro ao concluir o projeto: {str(e)}")

            return redirect('project_details', project_id=project_id)

    designer = project.project_designer
    manager = project.project_manager
    # Buscar sócio/franqueado da unidade (usuário com role de sócio ou franqueado)
    partner = User.objects.filter(
        units=project.unit, 
        roles__code__in=['socio_unidade', 'franqueado']
    ).first()
    credit_lines = CreditLine.objects.filter(enterprise=project.enterprise)
    banks = Bank.objects.filter(enterprise=project.enterprise)
    project_documents = ProjectDocument.objects.filter(project=project)
    project_history = ProjectHistory.objects.filter(project=project).order_by('-timestamp')

    return render(request, 'projects/project_details.html', {
        'project': project,
        'is_completed': project.project_finalized,
        'completed_statuses': completed_statuses,
        'designer': designer,
        'manager': manager,
        'partner': partner,
        'credit_lines': credit_lines,
        'banks': banks,
        'size_choices': SIZE_CHOICES,
        'activity_choices': ACTIVITY_CHOICES,
        'project_documents': project_documents,
        'project_history': project_history,
    })