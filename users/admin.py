from django.contrib import admin
from django.contrib.auth.models import Permission
from .models import User, Role, SystemModule
from units.models import Unit
from enterprises.models import Enterprise, Client, ClientDocument, ClientHistory
from projects.models import Project, ProjectHistory, ProjectDocument, CreditLine, Bank
# Importações de métricas removidas - será refeito

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')

class SystemModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'icon', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    list_editable = ('order', 'is_active')

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'enterprise', 'get_units_display', 'date_of_birth', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'enterprise', 'theme_preference')
    search_fields = ('email', 'name', 'cpf')
    filter_horizontal = ('roles', 'custom_permissions', 'groups', 'user_permissions', 'units')
    
    def get_units_display(self, obj):
        """Mostra as unidades do usuário no admin"""
        units = obj.units.all()
        if units:
            return ", ".join([unit.name for unit in units])
        return "Nenhuma unidade"
    get_units_display.short_description = 'Unidades'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('email', 'name', 'cpf', 'phone', 'date_of_birth', 'profile_image')
        }),
        ('Preferências', {
            'fields': ('theme_preference',)
        }),
        ('Organização', {
            'fields': ('enterprise', 'units')
        }),
        ('Sistema de Permissões', {
            'fields': ('roles', 'custom_permissions')
        }),
        ('Permissões Django', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )

# Registrar modelos
admin.site.register(User, UserAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(SystemModule, SystemModuleAdmin)

# Outros modelos
admin.site.register(Unit)
admin.site.register(Enterprise)
admin.site.register(Project)
# Cliente com inline de contas bancárias será registrado abaixo
admin.site.register(ClientDocument)
admin.site.register(ClientHistory)
admin.site.register(ProjectHistory)
admin.site.register(ProjectDocument)
admin.site.register(CreditLine)
admin.site.register(Bank)

# Registro personalizado do Client com inline de contas bancárias
from enterprises.models import ClientBankAccount

class ClientBankAccountInline(admin.TabularInline):
    model = ClientBankAccount
    extra = 0
    fields = ['bank', 'agency', 'account_number', 'account_type', 'is_active']

@admin.register(Client)
class ClientAdminWithBankAccounts(admin.ModelAdmin):
    list_display = ['name', 'email', 'cpf', 'status', 'enterprise', 'is_active', 'created_at']
    list_filter = ['status', 'enterprise', 'is_active', 'producer_classification', 'activity']
    search_fields = ['name', 'email', 'cpf', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['units']
    inlines = [ClientBankAccountInline]

# Registros de métricas removidos - será refeito

