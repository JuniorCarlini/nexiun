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
    list_display = ('email', 'name', 'enterprise', 'unit', 'date_of_birth', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'enterprise', 'theme_preference')
    search_fields = ('email', 'name', 'cpf')
    filter_horizontal = ('roles', 'custom_permissions', 'groups', 'user_permissions')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('email', 'name', 'cpf', 'phone', 'date_of_birth', 'profile_image')
        }),
        ('Preferências', {
            'fields': ('theme_preference',)
        }),
        ('Organização', {
            'fields': ('enterprise', 'unit')
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
admin.site.register(Client)
admin.site.register(ClientDocument)
admin.site.register(ClientHistory)
admin.site.register(ProjectHistory)
admin.site.register(ProjectDocument)
admin.site.register(CreditLine)
admin.site.register(Bank)

# Registros de métricas removidos - será refeito

