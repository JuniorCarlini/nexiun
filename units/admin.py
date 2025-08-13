from django.contrib import admin
from .models import BankAccount, Transaction

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'bank_name', 'account_type', 'enterprise', 'unit', 'get_current_balance', 'is_active')
    list_filter = ('account_type', 'is_active', 'enterprise', 'bank_name')
    search_fields = ('name', 'bank_name', 'account_number', 'enterprise__name')
    ordering = ('-created_at',)
    readonly_fields = ('get_current_balance', 'created_at', 'updated_at')

    def get_current_balance(self, obj):
        return f"R$ {obj.get_current_balance():.2f}"
    get_current_balance.short_description = 'Saldo Atual'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'transaction_type', 'category', 'amount', 'bank_account', 'unit', 'date', 'is_active')
    list_filter = ('transaction_type', 'category', 'is_active', 'unit__enterprise', 'bank_account', 'date')
    search_fields = ('description', 'notes', 'unit__name', 'bank_account__name')
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
