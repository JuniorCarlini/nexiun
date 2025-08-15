from django.contrib import admin
from .models import ReportCache, ReportSettings, ScheduledReport


@admin.register(ReportCache)
class ReportCacheAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'enterprise', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['report_type', 'enterprise', 'created_at', 'expires_at']
    search_fields = ['report_type', 'enterprise__name']
    readonly_fields = ['created_at', 'filter_hash']
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'


@admin.register(ReportSettings)
class ReportSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_period_days', 'auto_refresh_enabled', 'email_reports_enabled', 'email_frequency']
    list_filter = ['auto_refresh_enabled', 'email_reports_enabled', 'email_frequency']
    search_fields = ['user__name', 'user__email']
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Configurações Gerais', {
            'fields': ('default_period_days', 'auto_refresh_enabled', 'auto_refresh_interval')
        }),
        ('Email Reports', {
            'fields': ('email_reports_enabled', 'email_frequency')
        }),
        ('Metas', {
            'fields': ('target_proposals_month', 'target_approval_time_days', 'target_conversion_rate', 'target_repurchase_rate')
        }),
    )


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_type', 'frequency', 'next_run', 'is_active']
    list_filter = ['frequency', 'is_active', 'report_type']
    search_fields = ['user__name', 'user__email', 'report_type']
    readonly_fields = ['created_at', 'updated_at']
