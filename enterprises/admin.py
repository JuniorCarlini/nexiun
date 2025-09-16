from django.contrib import admin
from .models import ClientBankAccount

# Apenas o inline para ClientBankAccount será mantido aqui
# Os outros modelos serão gerenciados em seus respectivos apps

class ClientBankAccountInline(admin.TabularInline):
    model = ClientBankAccount
    extra = 0
    fields = ['bank', 'agency', 'account_number', 'account_type', 'is_active']


@admin.register(ClientBankAccount)
class ClientBankAccountAdmin(admin.ModelAdmin):
    list_display = ['client', 'bank', 'agency', 'account_number', 'account_type', 'is_active', 'created_at']
    list_filter = ['bank', 'account_type', 'is_active', 'created_at']
    search_fields = ['client__name', 'client__email', 'bank__name', 'agency', 'account_number']
    readonly_fields = ['created_at', 'updated_at'] 