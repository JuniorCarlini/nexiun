from django.db import models
from django.utils import timezone
from enterprises.models import Enterprise

class Unit(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="units")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Porcentagens
    royalties_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, 
        verbose_name="Porcentagem de Royalties (%)"
    )
    marketing_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, 
        verbose_name="Porcentagem de Marketing (%)"
    )
    designers_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, 
        verbose_name="Porcentagem de Projetistas (%)"
    )
    collectors_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, 
        verbose_name="Porcentagem de Captadores (%)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
        ordering = ['name']

    def __str__(self):
        status = "Ativa" if self.is_active else "Inativa"
        return f"{self.name} ({status})"

    def get_balance(self):
        """Calcula o saldo atual da unidade"""
        from django.db.models import Sum, Q
        entradas = self.transactions.filter(transaction_type='ENTRADA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0
        saidas = self.transactions.filter(transaction_type='SAIDA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0
        return entradas - saidas

    def get_total_entradas(self):
        """Retorna o total de entradas"""
        from django.db.models import Sum
        return self.transactions.filter(transaction_type='ENTRADA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0

    def get_total_saidas(self):
        """Retorna o total de saídas"""
        from django.db.models import Sum
        return self.transactions.filter(transaction_type='SAIDA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0


# Modelo para Contas Bancárias
class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ('CORRENTE', 'Conta Corrente'),
        ('POUPANCA', 'Conta Poupança'),
        ('INVESTIMENTO', 'Conta de Investimento'),
        ('OUTROS', 'Outros'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Nome da Conta")
    bank_name = models.CharField(max_length=255, verbose_name="Nome do Banco")
    account_type = models.CharField(max_length=15, choices=ACCOUNT_TYPES, default='CORRENTE', verbose_name="Tipo de Conta")
    account_number = models.CharField(max_length=50, verbose_name="Número da Conta", blank=True, null=True)
    agency = models.CharField(max_length=20, verbose_name="Agência", blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Saldo Inicial")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="bank_accounts", verbose_name="Empresa")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="bank_accounts", verbose_name="Unidade", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"
        ordering = ['bank_name', 'name']

    def __str__(self):
        status = "Ativa" if self.is_active else "Inativa"
        return f"{self.bank_name} - {self.name} ({status})"

    def get_current_balance(self):
        """Calcula o saldo atual da conta"""
        from django.db.models import Sum
        entradas = self.transactions.filter(transaction_type='ENTRADA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0
        saidas = self.transactions.filter(transaction_type='SAIDA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0
        return self.initial_balance + entradas - saidas

    def get_total_entradas(self):
        """Retorna o total de entradas da conta"""
        from django.db.models import Sum
        return self.transactions.filter(transaction_type='ENTRADA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0

    def get_total_saidas(self):
        """Retorna o total de saídas da conta"""
        from django.db.models import Sum
        return self.transactions.filter(transaction_type='SAIDA', is_active=True).aggregate(
            total=Sum('amount'))['total'] or 0


TRANSACTION_TYPES = [
    ('ENTRADA', 'Entrada'),
    ('SAIDA', 'Saída'),
]

TRANSACTION_CATEGORIES = [
    ('RECEITA', 'Receita'),
    ('COMISSAO', 'Comissão'),
    ('BONUS', 'Bônus'),
    ('REEMBOLSO', 'Reembolso'),
    ('MATERIAL', 'Material de Escritório'),
    ('TRANSPORTE', 'Transporte'),
    ('ALIMENTACAO', 'Alimentação'),
    ('COMBUSTIVEL', 'Combustível'),
    ('MANUTENCAO', 'Manutenção'),
    ('MARKETING', 'Marketing'),
    ('TREINAMENTO', 'Treinamento'),
    ('SALARIO', 'Salário'),
    ('SALARIO_TOTAL', 'Salário Total'),
    ('RECEITA_CREDITO_RURAL', 'Receita Crédito Rural'),
    ('RECEITA_CONSORCIO', 'Receita Consórcio'),
    ('OUTROS', 'Outros'),
]

class Transaction(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='transactions', verbose_name='Unidade')
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions', verbose_name='Conta Bancária')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name='Tipo')
    category = models.CharField(max_length=25, choices=TRANSACTION_CATEGORIES, verbose_name='Categoria')
    description = models.CharField(max_length=255, verbose_name='Descrição')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor')
    date = models.DateField(default=timezone.now, verbose_name='Data')
    notes = models.TextField(blank=True, null=True, verbose_name='Observações')
    
    # Metadados
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_transactions', verbose_name='Criado por')
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ['-date', '-created_at']

    def __str__(self):
        tipo_icon = "+" if self.transaction_type == 'ENTRADA' else "-"
        status = "Ativa" if self.is_active else "Inativa"
        return f"{tipo_icon} R$ {self.amount} - {self.description} ({status})"

    def get_type_display_with_icon(self):
        if self.transaction_type == 'ENTRADA':
            return '<i class="fas fa-arrow-up text-success"></i> Entrada'
        else:
            return '<i class="fas fa-arrow-down text-danger"></i> Saída'
