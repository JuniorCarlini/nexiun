import json
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import datetime, timedelta, date
from users.decorators import permission_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Unit, Transaction, BankAccount, TRANSACTION_TYPES, TRANSACTION_CATEGORIES
from django.http import JsonResponse
from enterprises.models import Enterprise
from decimal import Decimal
from core.mixins import unit_filter_required, get_selected_unit_from_request, is_all_units_selected_from_request, get_accessible_units_from_request

# ==================== GESTÃO DE CONTAS BANCÁRIAS ====================

# Criar conta bancária
@login_required
@permission_required('users.add_bank_accounts')
def create_bank_account_view(request):
    # Obter informações da sessão e unidades
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Verificar se usuário tem acesso a unidades
    if not request.user.has_perm('users.view_all_units'):
        if not accessible_units.exists():
            messages.error(request, "Você precisa estar vinculado a pelo menos uma unidade para criar contas bancárias.")
            return redirect('dashboard_financeiro')

    if request.method == 'POST':
        # Verificar se está tentando criar com "Todas as unidades" selecionado
        if is_all_units_selected:
            messages.error(request, 'Para criar contas bancárias, você deve estar em uma unidade específica. Altere sua sessão antes de continuar.')
            return render(request, 'units/create_bank_account.html', {
                'form_data': request.POST,
                'account_types': BankAccount.ACCOUNT_TYPES,
                'accessible_units': accessible_units,
                'selected_unit': selected_unit,
                'is_all_units_selected': is_all_units_selected,
            })
            
        name = request.POST.get('name', '').strip()
        bank_name = request.POST.get('bank_name', '').strip()
        account_type = request.POST.get('account_type', 'CORRENTE')
        account_number = request.POST.get('account_number', '').strip()
        agency = request.POST.get('agency', '').strip()
        description = request.POST.get('description', '').strip()
        initial_balance = request.POST.get('initial_balance', '0').replace(',', '.')

        # Usar unidade da sessão
        unit = selected_unit
        if not unit:
            unit = accessible_units.first()

        # Validações
        errors = []
        if not name:
            errors.append('Nome da conta é obrigatório.')
        if not bank_name:
            errors.append('Nome do banco é obrigatório.')
        if not unit:
            errors.append('Usuário não está associado a nenhuma unidade.')
        
        try:
            initial_balance = float(initial_balance)
        except ValueError:
            errors.append('Saldo inicial deve ser um número válido.')

        if errors:
            for error in errors:
                messages.error(request, error)
            
            return render(request, 'units/create_bank_account.html', {
                'form_data': request.POST,
                'account_types': BankAccount.ACCOUNT_TYPES,
                'accessible_units': accessible_units,
                'selected_unit': selected_unit,
                'is_all_units_selected': is_all_units_selected,
            })

        try:
            BankAccount.objects.create(
                name=name,
                bank_name=bank_name,
                account_type=account_type,
                account_number=account_number,
                agency=agency,
                description=description,
                initial_balance=initial_balance,
                enterprise=request.user.enterprise,
                unit=unit
            )
            
            messages.success(request, 'Conta bancária criada com sucesso!')
            return redirect('dashboard_financeiro')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar conta bancária: {str(e)}')

    # GET request
    return render(request, 'units/create_bank_account.html', {
        'account_types': BankAccount.ACCOUNT_TYPES,
        'accessible_units': accessible_units,
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
    })

# Editar conta bancária
@login_required
@permission_required('users.change_bank_accounts')
def edit_bank_account_view(request, account_id):
    account = get_object_or_404(BankAccount, id=account_id, enterprise=request.user.enterprise)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        bank_name = request.POST.get('bank_name', '').strip()
        account_type = request.POST.get('account_type', 'CORRENTE')
        account_number = request.POST.get('account_number', '').strip()
        agency = request.POST.get('agency', '').strip()
        description = request.POST.get('description', '').strip()
        initial_balance_str = request.POST.get('initial_balance', '').strip()

        # Validações
        errors = []
        if not name:
            errors.append('Nome da conta é obrigatório.')
        if not bank_name:
            errors.append('Nome do banco é obrigatório.')
        
        # Validação do saldo inicial
        initial_balance = 0
        if initial_balance_str:
            try:
                initial_balance = float(initial_balance_str.replace(',', '.'))
            except ValueError:
                errors.append('Saldo inicial deve ser um número válido.')
        else:
            # Se não foi informado, mantém o valor atual
            initial_balance = account.initial_balance

        if errors:
            for error in errors:
                messages.error(request, error)
            
            return render(request, 'units/edit_bank_account.html', {
                'account': account,
                'form_data': request.POST,
                'account_types': BankAccount.ACCOUNT_TYPES,
            })

        try:
            account.name = name
            account.bank_name = bank_name
            account.account_type = account_type
            account.account_number = account_number
            account.agency = agency
            account.description = description
            account.initial_balance = initial_balance
            account.save()
            
            messages.success(request, 'Conta bancária atualizada com sucesso!')
            return redirect('dashboard_financeiro')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar conta bancária: {str(e)}')

    # GET request
    return render(request, 'units/edit_bank_account.html', {
        'account': account,
        'account_types': BankAccount.ACCOUNT_TYPES,
        'form_data': {
            'bank_name': account.bank_name,
            'name': account.name,
            'account_type': account.account_type,
            'agency': account.agency,
            'account_number': account.account_number,
            'initial_balance': account.initial_balance,
            'description': account.description,
        }
    })

# Ativar/Desativar conta bancária
@login_required
@permission_required('users.change_bank_accounts')
def toggle_bank_account_status_view(request, account_id):
    account = get_object_or_404(BankAccount, id=account_id, enterprise=request.user.enterprise)
    
    if request.method == 'POST':
        account.is_active = not account.is_active
        account.save()
        
        status_text = "ativada" if account.is_active else "desativada"
        messages.success(request, f'Conta "{account.name}" foi {status_text} com sucesso!')
    
    return redirect('dashboard_financeiro')

# ==================== UNIDADES ====================

# Cria uma unidade
@login_required
@permission_required('users.manage_units_master')
def create_unit_view(request):
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        
        # Capturar campos de porcentagem
        royalties_percentage = request.POST.get('royalties_percentage', '0')
        marketing_percentage = request.POST.get('marketing_percentage', '0')
        designers_percentage = request.POST.get('designers_percentage', '0')
        collectors_percentage = request.POST.get('collectors_percentage', '0')
        
        # Validação básica
        if not name or not location:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'units/create_unit.html', {
                'name': name,
                'location': location,
                'royalties_percentage': royalties_percentage,
                'marketing_percentage': marketing_percentage,
                'designers_percentage': designers_percentage,
                'collectors_percentage': collectors_percentage
            })
        
        # Validação das porcentagens
        try:
            royalties_percentage = float(royalties_percentage) if royalties_percentage else 0
            marketing_percentage = float(marketing_percentage) if marketing_percentage else 0
            designers_percentage = float(designers_percentage) if designers_percentage else 0
            collectors_percentage = float(collectors_percentage) if collectors_percentage else 0
        except ValueError:
            messages.error(request, 'Por favor, insira valores válidos para as porcentagens.')
            return render(request, 'units/create_unit.html', {
                'name': name,
                'location': location,
                'royalties_percentage': request.POST.get('royalties_percentage', '0'),
                'marketing_percentage': request.POST.get('marketing_percentage', '0'),
                'designers_percentage': request.POST.get('designers_percentage', '0'),
                'collectors_percentage': request.POST.get('collectors_percentage', '0')
            })
        
        try:
            # Cria a unidade
            Unit.objects.create(
                name=name,
                location=location,
                enterprise=request.user.enterprise,
                royalties_percentage=royalties_percentage,
                marketing_percentage=marketing_percentage,
                designers_percentage=designers_percentage,
                collectors_percentage=collectors_percentage
            )
            
            messages.success(request, 'Unidade criada com sucesso!')
            return redirect('units_list')
            
        except Exception as e:
            messages.error(request, 'Erro ao criar unidade. Por favor, tente novamente.')
            return render(request, 'units/create_unit.html', {
                'name': name,
                'location': location,
                'royalties_percentage': royalties_percentage,
                'marketing_percentage': marketing_percentage,
                'designers_percentage': designers_percentage,
                'collectors_percentage': collectors_percentage
            })
    
    return render(request, 'units/create_unit.html')

# Edita uma unidade
@login_required
@permission_required('users.manage_units_master')
def units_edit_view(request, unit_id):
    
    # Garantir que o usuário só pode editar unidades da sua própria empresa
    unit = get_object_or_404(Unit, id=unit_id, enterprise=request.user.enterprise)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        
        # Capturar campos de porcentagem
        royalties_percentage = request.POST.get('royalties_percentage', '0')
        marketing_percentage = request.POST.get('marketing_percentage', '0')
        designers_percentage = request.POST.get('designers_percentage', '0')
        collectors_percentage = request.POST.get('collectors_percentage', '0')
        
        # Validação básica
        if not name or not location:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'units/edit_unit.html', {
                'unit': unit,
                'name': name,
                'location': location,
                'royalties_percentage': royalties_percentage,
                'marketing_percentage': marketing_percentage,
                'designers_percentage': designers_percentage,
                'collectors_percentage': collectors_percentage
            })
        
        # Validação das porcentagens
        try:
            royalties_percentage = float(royalties_percentage) if royalties_percentage else 0
            marketing_percentage = float(marketing_percentage) if marketing_percentage else 0
            designers_percentage = float(designers_percentage) if designers_percentage else 0
            collectors_percentage = float(collectors_percentage) if collectors_percentage else 0
        except ValueError:
            messages.error(request, 'Por favor, insira valores válidos para as porcentagens.')
            return render(request, 'units/edit_unit.html', {
                'unit': unit,
                'name': name,
                'location': location,
                'royalties_percentage': request.POST.get('royalties_percentage', '0'),
                'marketing_percentage': request.POST.get('marketing_percentage', '0'),
                'designers_percentage': request.POST.get('designers_percentage', '0'),
                'collectors_percentage': request.POST.get('collectors_percentage', '0')
            })
        
        try:
            unit.name = name
            unit.location = location
            unit.royalties_percentage = royalties_percentage
            unit.marketing_percentage = marketing_percentage
            unit.designers_percentage = designers_percentage
            unit.collectors_percentage = collectors_percentage
            unit.save()
            
            messages.success(request, 'Unidade atualizada com sucesso!')
            return redirect('units_list')
            
        except Exception as e:
            messages.error(request, 'Erro ao atualizar unidade. Por favor, tente novamente.')
            return render(request, 'units/edit_unit.html', {
                'unit': unit,
                'name': name,
                'location': location,
                'royalties_percentage': royalties_percentage,
                'marketing_percentage': marketing_percentage,
                'designers_percentage': designers_percentage,
                'collectors_percentage': collectors_percentage
            })
    
    # GET request - mostrar formulário
    return render(request, 'units/edit_unit.html', {
        'unit': unit,
        'name': unit.name,
        'location': unit.location,
        'royalties_percentage': unit.royalties_percentage,
        'marketing_percentage': unit.marketing_percentage,
        'designers_percentage': unit.designers_percentage,
        'collectors_percentage': unit.collectors_percentage
    })

# Lista as unidades
@login_required
@permission_required('users.view_units')
def units_list_view(request):
    
    # Configurar a paginação
    page = request.GET.get('page', 1)
    units = Unit.objects.filter(enterprise=request.user.enterprise).order_by('-is_active', 'name')  # Ativas primeiro, depois por nome
    paginator = Paginator(units, 20)
    
    try:
        units_page = paginator.page(page)
    except PageNotAnInteger:
        units_page = paginator.page(1)
    except EmptyPage:
        units_page = paginator.page(paginator.num_pages)
    
    return render(request, 'units/list_units.html', {
        'units': units_page
    })

# Ativa/Desativa uma unidade (ao invés de excluir)
@login_required
@permission_required('users.change_units')
def toggle_unit_status_view(request, unit_id):
    # Garantir que o usuário só pode alterar unidades da sua própria empresa
    unit = get_object_or_404(Unit, id=unit_id, enterprise=request.user.enterprise)
    
    if request.method == 'POST':
        # Alterna o status da unidade
        unit.is_active = not unit.is_active
        unit.save()
        
        status_text = "ativada" if unit.is_active else "desativada"
        messages.success(request, f'Unidade "{unit.name}" foi {status_text} com sucesso!')
    
    return redirect('units_list')


# ==================== SISTEMA FINANCEIRO DAS UNIDADES ====================

# Lista de transações da unidade
@login_required
@permission_required('users.view_unit_transactions')
def unit_transactions_list_view(request, unit_id=None):
    # Se unit_id não for fornecido, usar a unidade do usuário
    if unit_id:
        # Verificar se pode ver todas as unidades ou apenas a própria
        if request.user.has_perm('users.view_all_unit_transactions'):
            unit = get_object_or_404(Unit, id=unit_id, enterprise=request.user.enterprise)
        else:
            # Só pode ver as próprias unidades
            user_units = request.user.units.all()
            if not user_units.exists():
                messages.error(request, 'Você não está associado a nenhuma unidade.')
                return redirect('home')
            if unit_id not in user_units.values_list('id', flat=True):
                messages.error(request, 'Você não tem permissão para acessar esta unidade.')
                return redirect('home')
            unit = get_object_or_404(Unit, id=unit_id, enterprise=request.user.enterprise)
    else:
        # Se não especificou unit_id, usar a primeira unidade do usuário
        unit = request.user.units.first()
        if not unit:
            messages.error(request, 'Você não está associado a nenhuma unidade.')
            return redirect('home')
    
    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    categoria_filtro = request.GET.get('categoria', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Buscar transações
    transactions = Transaction.objects.filter(unit=unit, is_active=True)
    
    # Aplicar filtros
    if tipo_filtro:
        transactions = transactions.filter(transaction_type=tipo_filtro)
    if categoria_filtro:
        transactions = transactions.filter(category=categoria_filtro)
    if data_inicio:
        transactions = transactions.filter(date__gte=data_inicio)
    if data_fim:
        transactions = transactions.filter(date__lte=data_fim)
    
    # Ordenar transações por data (mais recentes primeiro) e depois por ID
    transactions = transactions.order_by('-date', '-id')
    
    # Paginação
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    
    try:
        transactions_page = paginator.page(page_number)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    
    context = {
        'unit': unit,
        'transactions': transactions_page,
        'transaction_types': TRANSACTION_TYPES,
        'transaction_categories': TRANSACTION_CATEGORIES,
        'filtros': {
            'tipo': tipo_filtro,
            'categoria': categoria_filtro,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'units/transactions_list.html', context)


# Adicionar transação
@login_required
@permission_required('users.add_unit_transactions')
def add_transaction_view(request, unit_id=None):
    # Obter informações da sessão e unidades
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Verificar se usuário tem acesso a unidades
    if not request.user.has_perm('users.view_all_units'):
        if not accessible_units.exists():
            messages.error(request, "Você precisa estar vinculado a pelo menos uma unidade para criar transações.")
            return redirect('home')
    
    # Se "Todas as unidades" estiver selecionado, não permitir criação de transação
    if is_all_units_selected:
        messages.warning(request, 'Para criar transações, você deve selecionar uma unidade específica. Altere sua sessão antes de continuar.')
        return redirect('dashboard_financeiro')
    
    # Usar unidade específica selecionada na sessão
    unit = selected_unit
    if not unit:
        unit = accessible_units.first()
    
    if not unit:
        messages.error(request, 'Nenhuma unidade disponível para criar transações.')
        return redirect('home')
    
    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')
        category = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        amount = request.POST.get('amount', '').replace(',', '.')
        transaction_date = request.POST.get('date')
        notes = request.POST.get('notes', '').strip()
        bank_account_id = request.POST.get('bank_account')
        
        # Validações
        errors = []
        if not transaction_type or transaction_type not in [t[0] for t in TRANSACTION_TYPES]:
            errors.append('Tipo de transação é obrigatório e deve ser válido.')
        if not category or category not in [c[0] for c in TRANSACTION_CATEGORIES]:
            errors.append('Categoria é obrigatória e deve ser válida.')
        if not description:
            errors.append('Descrição é obrigatória.')
        if not amount:
            errors.append('Valor é obrigatório.')
        else:
            try:
                amount = float(amount)
                if amount <= 0:
                    errors.append('Valor deve ser maior que zero.')
            except ValueError:
                errors.append('Valor deve ser um número válido.')
        if not transaction_date:
            errors.append('Data é obrigatória.')
        if not bank_account_id:
            errors.append('Conta bancária é obrigatória.')
        else:
            try:
                bank_account = BankAccount.objects.get(id=bank_account_id, enterprise=request.user.enterprise, is_active=True)
            except BankAccount.DoesNotExist:
                errors.append('Conta bancária inválida.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            bank_accounts = BankAccount.objects.filter(enterprise=request.user.enterprise, is_active=True)
            return render(request, 'units/add_transaction.html', {
                'unit': unit,
                'transaction_types': TRANSACTION_TYPES,
                'transaction_categories': TRANSACTION_CATEGORIES,
                'bank_accounts': bank_accounts,
                'form_data': request.POST,
                'today': date.today(),
            })
        
        try:
            Transaction.objects.create(
                unit=unit,
                bank_account=bank_account,
                transaction_type=transaction_type,
                category=category,
                description=description,
                amount=amount,
                date=transaction_date,
                notes=notes,
                created_by=request.user
            )
            
            tipo_text = 'entrada' if transaction_type == 'ENTRADA' else 'saída'
            messages.success(request, f'Transação de {tipo_text} criada com sucesso!')
            return redirect('unit_transactions_list', unit_id=unit.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao criar transação: {str(e)}')
    
    # Buscar contas bancárias ativas da empresa
    bank_accounts = BankAccount.objects.filter(enterprise=request.user.enterprise, is_active=True)
    
    context = {
        'unit': unit,
        'transaction_types': TRANSACTION_TYPES,
        'transaction_categories': TRANSACTION_CATEGORIES,
        'bank_accounts': bank_accounts,
        'today': date.today(),
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
    }
    
    return render(request, 'units/add_transaction.html', context)


# Editar transação
@login_required
@permission_required('users.change_unit_transactions')
def edit_transaction_view(request, transaction_id):
    # Obter informações da sessão
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Verificar se pode editar transações de outras unidades
    if request.user.has_perm('users.view_all_unit_transactions'):
        transaction = get_object_or_404(Transaction, id=transaction_id, unit__enterprise=request.user.enterprise)
    else:
        transaction = get_object_or_404(Transaction, id=transaction_id, unit__in=accessible_units, unit__enterprise=request.user.enterprise)
    
    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')
        category = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        amount = request.POST.get('amount', '').replace(',', '.')
        transaction_date = request.POST.get('date')
        notes = request.POST.get('notes', '').strip()
        bank_account_id = request.POST.get('bank_account')
        
        # Validações (igual ao add)
        errors = []
        if not transaction_type or transaction_type not in [t[0] for t in TRANSACTION_TYPES]:
            errors.append('Tipo de transação é obrigatório e deve ser válido.')
        if not category or category not in [c[0] for c in TRANSACTION_CATEGORIES]:
            errors.append('Categoria é obrigatória e deve ser válida.')
        if not description:
            errors.append('Descrição é obrigatória.')
        if not amount:
            errors.append('Valor é obrigatório.')
        else:
            try:
                amount = float(amount)
                if amount <= 0:
                    errors.append('Valor deve ser maior que zero.')
            except ValueError:
                errors.append('Valor deve ser um número válido.')
        if not transaction_date:
            errors.append('Data é obrigatória.')
        if not bank_account_id:
            errors.append('Conta bancária é obrigatória.')
        else:
            try:
                bank_account = BankAccount.objects.get(id=bank_account_id, enterprise=request.user.enterprise, is_active=True)
            except BankAccount.DoesNotExist:
                errors.append('Conta bancária inválida.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            bank_accounts = BankAccount.objects.filter(enterprise=request.user.enterprise, is_active=True)
            return render(request, 'units/edit_transaction.html', {
                'transaction': transaction,
                'transaction_types': TRANSACTION_TYPES,
                'transaction_categories': TRANSACTION_CATEGORIES,
                'bank_accounts': bank_accounts,
                'form_data': request.POST,
            })
        
        try:
            transaction.transaction_type = transaction_type
            transaction.category = category
            transaction.description = description
            transaction.amount = amount
            transaction.date = transaction_date
            transaction.notes = notes
            transaction.bank_account = bank_account
            transaction.save()
            
            messages.success(request, 'Transação atualizada com sucesso!')
            return redirect('unit_transactions_list', unit_id=transaction.unit.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar transação: {str(e)}')
    
    # Buscar contas bancárias ativas da empresa
    bank_accounts = BankAccount.objects.filter(enterprise=request.user.enterprise, is_active=True)
    
    context = {
        'transaction': transaction,
        'transaction_types': TRANSACTION_TYPES,
        'transaction_categories': TRANSACTION_CATEGORIES,
        'bank_accounts': bank_accounts,
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
    }
    
    return render(request, 'units/edit_transaction.html', context)


# Excluir/desativar transação
@login_required
@permission_required('users.delete_unit_transactions')
def delete_transaction_view(request, transaction_id):
    # Obter informações da sessão
    accessible_units = get_accessible_units_from_request(request)
    
    # Verificar se pode excluir transações de outras unidades
    if request.user.has_perm('users.view_all_unit_transactions'):
        transaction = get_object_or_404(Transaction, id=transaction_id, unit__enterprise=request.user.enterprise)
    else:
        transaction = get_object_or_404(Transaction, id=transaction_id, unit__in=accessible_units, unit__enterprise=request.user.enterprise)
    
    if request.method == 'POST':
        transaction.is_active = False
        transaction.save()
        
        messages.success(request, 'Transação excluída com sucesso!')
        return redirect('unit_transactions_list', unit_id=transaction.unit.id)
    
    return render(request, 'units/delete_transaction.html', {'transaction': transaction})


# Dashboard Financeiro - Novo estilo
@login_required
@permission_required('users.view_unit_financial_dashboard')
def financial_dashboard_new_view(request, unit_id=None):
    """Dashboard financeiro no estilo moderno"""
    
    # Obter informações da sessão e unidades
    accessible_units = get_accessible_units_from_request(request)
    selected_unit = get_selected_unit_from_request(request)
    is_all_units_selected = is_all_units_selected_from_request(request)
    
    # Verificar se usuário tem acesso a unidades (nova lógica)
    # Usuários com view_unit_financial_dashboard podem acessar sem estar vinculados a unidades
    if not request.user.has_perm('users.view_all_units') and not request.user.has_perm('users.view_unit_financial_dashboard'):
        if not accessible_units.exists():
            messages.error(request, "Você precisa estar vinculado a pelo menos uma unidade para acessar o dashboard financeiro.")
            return redirect('home')
    
    # Se "Todas as unidades" estiver selecionado, mostrar dados consolidados ou redirecionar
    if is_all_units_selected:
        # Por enquanto, vamos usar a primeira unidade disponível para evitar erro
        # Futuramente pode ser implementado um dashboard consolidado
        if request.user.has_perm('users.view_all_units') or request.user.has_perm('users.view_unit_financial_dashboard'):
            unit = accessible_units.first()
            if not unit:
                messages.error(request, 'Nenhuma unidade encontrada na empresa.')
                return redirect('home')
        else:
            messages.warning(request, 'Selecione uma unidade específica para ver o dashboard financeiro.')
            return redirect('home')
    else:
        # Usar unidade específica selecionada na sessão
        unit = selected_unit
        if not unit:
            unit = accessible_units.first()
        
        if not unit:
            messages.error(request, 'Nenhuma unidade disponível para visualizar.')
            return redirect('home')
    
    # Calcular saldo atual
    saldo_atual = unit.get_balance()
    total_entradas = unit.get_total_entradas()
    total_saidas = unit.get_total_saidas()
    
    # Situação mensal (comparação com mês anterior)
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    
    # Entradas e saídas do mês atual
    current_month_entradas = Transaction.objects.filter(
        unit=unit, 
        transaction_type='ENTRADA', 
        is_active=True,
        date__gte=current_month_start,
        date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    current_month_saidas = Transaction.objects.filter(
        unit=unit, 
        transaction_type='SAIDA', 
        is_active=True,
        date__gte=current_month_start,
        date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Entradas e saídas do mês anterior
    last_month_entradas = Transaction.objects.filter(
        unit=unit, 
        transaction_type='ENTRADA', 
        is_active=True,
        date__gte=last_month_start,
        date__lte=last_month_end
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    last_month_saidas = Transaction.objects.filter(
        unit=unit, 
        transaction_type='SAIDA', 
        is_active=True,
        date__gte=last_month_start,
        date__lte=last_month_end
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calcular situação mensal (comparação)
    current_month_saldo = current_month_entradas - current_month_saidas
    last_month_saldo = last_month_entradas - last_month_saidas
    situacao_mensal = current_month_saldo - last_month_saldo
    
    # Dados para gráfico de barras (últimos 6 meses)
    meses_dados = []
    meses_labels = []
    entradas_chart = []
    saidas_chart = []
    
    for i in range(5, -1, -1):
        mes_data = today - timedelta(days=30 * i)
        mes_inicio = mes_data.replace(day=1)
        if i == 0:
            mes_fim = today
        else:
            mes_fim = (mes_data.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        entradas_mes = Transaction.objects.filter(
            unit=unit, 
            transaction_type='ENTRADA', 
            is_active=True,
            date__gte=mes_inicio,
            date__lte=mes_fim
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        saidas_mes = Transaction.objects.filter(
            unit=unit, 
            transaction_type='SAIDA', 
            is_active=True,
            date__gte=mes_inicio,
            date__lte=mes_fim
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        meses_labels.append(mes_data.strftime('%b'))
        entradas_chart.append(float(entradas_mes))
        saidas_chart.append(float(saidas_mes))
    
    # Dados para gráfico de pizza (gastos por categoria do mês atual)
    categorias_gastos = []
    valores_gastos = []
    
    gastos_por_categoria = Transaction.objects.filter(
        unit=unit, 
        transaction_type='SAIDA', 
        is_active=True,
        date__gte=current_month_start,
        date__lte=today
    ).values('category').annotate(total=Sum('amount')).order_by('-total')
    
    for gasto in gastos_por_categoria:
        categoria_display = dict(TRANSACTION_CATEGORIES).get(gasto['category'], gasto['category'])
        categorias_gastos.append(categoria_display)
        valores_gastos.append(float(gasto['total']))
    
    # Contas bancárias
    contas_bancarias = BankAccount.objects.filter(
        enterprise=request.user.enterprise, 
        is_active=True
    ).filter(
        Q(unit=unit) | Q(unit__isnull=True)
    )
    
    # Transações recentes com paginação
    transacoes_queryset = Transaction.objects.filter(
        unit=unit, 
        is_active=True
    ).select_related('bank_account').order_by('-date', '-id')
    
    # Paginação
    page = request.GET.get('page', 1)
    paginator = Paginator(transacoes_queryset, 10)  # 10 transações por página
    
    try:
        transacoes_recentes = paginator.page(page)
    except PageNotAnInteger:
        transacoes_recentes = paginator.page(1)
    except EmptyPage:
        transacoes_recentes = paginator.page(paginator.num_pages)
    
    context = {
        'unit': unit,
        'enterprise': request.user.enterprise,
        
        # Métricas principais
        'saldo_atual': saldo_atual,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'situacao_mensal': situacao_mensal,
        'current_month_entradas': current_month_entradas,
        'current_month_saidas': current_month_saidas,
        
        # Dados para gráficos (em formato JSON)
        'meses_labels': json.dumps(meses_labels),
        'entradas_chart': json.dumps(entradas_chart),
        'saidas_chart': json.dumps(saidas_chart),
        'categorias_gastos': json.dumps(categorias_gastos),
        'valores_gastos': json.dumps(valores_gastos),
        
        # Outros dados
        'contas_bancarias': contas_bancarias,
        'transacoes_recentes': transacoes_recentes,
        
        # Variáveis de sessão para template
        'selected_unit': selected_unit,
        'is_all_units_selected': is_all_units_selected,
    }
    
    return render(request, 'units/dashboard_financeiro.html', context)

# EXEMPLO DE USO DO NOVO SISTEMA:
# Lista de transações usando unidade selecionada na sessão
@login_required
@unit_filter_required
@permission_required('users.view_unit_transactions')
def unit_transactions_list_session_view(request):
    """
    View de exemplo usando o sistema de sessão para filtrar transações
    """
    # Obter unidade selecionada na sessão
    selected_unit = get_selected_unit_from_request(request)
    
    if not selected_unit:
        messages.error(request, 'Nenhuma unidade selecionada.')
        return redirect('home')
    
    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    categoria_filtro = request.GET.get('categoria', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Buscar transações da unidade selecionada
    transactions = Transaction.objects.filter(unit=selected_unit, is_active=True)
    
    # Aplicar filtros
    if tipo_filtro:
        transactions = transactions.filter(transaction_type=tipo_filtro)
    if categoria_filtro:
        transactions = transactions.filter(category=categoria_filtro)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            transactions = transactions.filter(date__gte=data_inicio_obj)
        except ValueError:
            messages.warning(request, 'Data de início inválida.')
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            transactions = transactions.filter(date__lte=data_fim_obj)
        except ValueError:
            messages.warning(request, 'Data de fim inválida.')
    
    # Ordenar por data
    transactions = transactions.order_by('-date', '-created_at')
    
    # Paginação
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular totais
    total_entradas = transactions.filter(transaction_type='ENTRADA').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    total_saidas = transactions.filter(transaction_type='SAIDA').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    saldo_periodo = total_entradas - total_saidas
    
    context = {
        'transactions': page_obj,
        'selected_unit': selected_unit,
        'transaction_types': TRANSACTION_TYPES,
        'transaction_categories': TRANSACTION_CATEGORIES,
        'tipo_filtro': tipo_filtro,
        'categoria_filtro': categoria_filtro,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_periodo': saldo_periodo,
    }
    
    return render(request, 'units/transactions_list.html', context)