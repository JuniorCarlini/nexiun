from django.db import models
from django.utils import timezone
from users.models import User
from enterprises.models import Enterprise
from units.models import Unit


class ReportCache(models.Model):
    """Cache para armazenar dados calculados de relatórios"""
    report_type = models.CharField(max_length=50, verbose_name="Tipo de Relatório")
    filter_hash = models.CharField(max_length=64, verbose_name="Hash dos Filtros")
    data = models.JSONField(verbose_name="Dados do Relatório")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="Empresa")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name="Expira em")
    
    class Meta:
        verbose_name = "Cache de Relatório"
        verbose_name_plural = "Cache de Relatórios"
        unique_together = ['report_type', 'filter_hash', 'enterprise']
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class ReportSettings(models.Model):
    """Configurações personalizadas de relatórios por usuário"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='report_settings')
    default_period_days = models.IntegerField(default=365, verbose_name="Período Padrão (dias)")
    auto_refresh_enabled = models.BooleanField(default=True, verbose_name="Atualização Automática")
    auto_refresh_interval = models.IntegerField(default=60, verbose_name="Intervalo de Atualização (min)")
    email_reports_enabled = models.BooleanField(default=False, verbose_name="Relatórios por Email")
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Diário'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensal'),
        ],
        default='weekly',
        verbose_name="Frequência dos Emails"
    )
    
    # Metas personalizadas
    target_proposals_month = models.IntegerField(null=True, blank=True, verbose_name="Meta Propostas/Mês")
    target_approval_time_days = models.IntegerField(null=True, blank=True, verbose_name="Meta Tempo Aprovação (dias)")
    target_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Meta Taxa Conversão (%)")
    target_repurchase_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Meta Taxa Recompra (%)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração de Relatório"
        verbose_name_plural = "Configurações de Relatórios"


class ScheduledReport(models.Model):
    """Relatórios agendados para envio por email"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    report_type = models.CharField(max_length=50, verbose_name="Tipo de Relatório")
    filters = models.JSONField(default=dict, verbose_name="Filtros")
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Diário'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensal'),
        ],
        verbose_name="Frequência"
    )
    next_run = models.DateTimeField(verbose_name="Próxima Execução")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Relatório Agendado"
        verbose_name_plural = "Relatórios Agendados"
