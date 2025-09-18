import os
import uuid
from django.db import models
from users.models import User
from units.models import Unit
from django.utils import timezone
from django.contrib.auth import get_user_model
from enterprises.models import Enterprise, Client
from django.core.serializers.json import DjangoJSONEncoder


PROJECT_STATUS_CHOICES = [
    ('AC', 'Em Acolhimento'),
    ('PE', 'Com Pendência'),
    ('AN', 'Em Análise'),
    ('AP', 'Aprovados'),
    ('AF', 'Em Formalização'),
    ('FM', 'Formalizado'),
    ('LB', 'Liberado'),
    ('RC', 'Receita'),
]

ACTIVITY_CHOICES = [
    ('AGR', 'Agricultura'),
    ('PEC', 'Pecuária'),
    ('OUT', 'Outros'),
]

SIZE_CHOICES = [
    ('PQ', 'Pequeno'),
    ('MD', 'Médio'),
    ('GD', 'Grande'),
]

TYPE_CHOICES = [
    ('CUS', 'Custeio'),
    ('INV', 'Investimento'),
    ('PRO', 'Prorrogação'),
    ('CPR', 'CPR'),
    ('OTH', 'Outros'),
]

def project_document_directory_path(instance, filename):
    unique_filename = f"{uuid.uuid4()}.{filename.split('.')[-1]}"
    return f'project_documents/{instance.project.client.id}/{instance.project.id}/{unique_filename}'

# Linhas de crédito
class CreditLine(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type_credit = models.CharField(max_length=3, choices=TYPE_CHOICES, default='CUS')
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='credit_lines')
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Linha de Crédito"
        verbose_name_plural = "Linhas de Crédito"
        ordering = ['name']
    
    def __str__(self):
        status = "Ativa" if self.is_active else "Inativa"
        return f"{self.name} - {self.get_type_credit_display()} ({status})"

# Bancos
class Bank(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='banks')
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"
        ordering = ['name']
    
    def __str__(self):
        status = "Ativo" if self.is_active else "Inativo"
        return f"{self.name} - {self.enterprise.name} ({status})"

# TODO de aprovado pra frente todos os campos se tornam obrigatórios

# Projetos
class Project(models.Model):
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=2, choices=PROJECT_STATUS_CHOICES, default='AC')
    client = models.ForeignKey('enterprises.Client', on_delete=models.CASCADE, related_name="projects")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE,null=True, related_name="projects")
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="projects")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="projects")
    credit_line = models.ForeignKey(CreditLine, on_delete=models.CASCADE, related_name="projects")
    project_manager = models.ForeignKey(User, blank=True, on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    project_designer = models.ForeignKey(User, blank=True, on_delete=models.SET_NULL, null=True, related_name='designed_projects')
    project_prospector = models.ForeignKey(User, blank=True, on_delete=models.SET_NULL, null=True, related_name='prospected_projects')
    land_size = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Tamanho da Terra (ha)")
    size = models.CharField(max_length=2, blank=True, choices=SIZE_CHOICES, verbose_name="Tamanho do Projeto")
    activity = models.CharField(max_length=3, blank=True, choices=ACTIVITY_CHOICES, verbose_name="Atividade")
    documents_description = models.TextField(blank=True, null=True, verbose_name="Descrição de Documentos")
    next_phase_deadline = models.DateField(blank=True, null=True, verbose_name="Prazo Estimado Próxima Fase")
    installments = models.IntegerField(blank=True, null=True, verbose_name="Parcelas")
    fees = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Juros")
    payment_grace = models.IntegerField(blank=True, null=True, verbose_name="Carência para pagamento")
    project_deadline = models.IntegerField(blank=True, null=True, verbose_name="Prazo para pagamento do Projeto")
    value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor do Projeto")
    percentage_astec = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Porcentagem ASTEC")
    approval_date = models.DateField(blank=True, null=True, verbose_name="Data de Aprovação")
    consortium_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor do Consórcio")
    first_installment_date = models.DateField(blank=True, null=True, verbose_name="Data Primeira Parcela")
    last_installment_date = models.DateField(blank=True, null=True, verbose_name="Data Última Parcela")
    project_finalized = models.BooleanField(default=False, verbose_name="Projeto Finalizado")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ['-created_at']

    def __str__(self):
        status = "Ativo" if self.is_active else "Inativo"
        return f"{self.credit_line.name} - {self.client.name} ({status})"

#TODO: Criar um model para armazenar as alterações feitas no projeto

# Histórico de alterações no projeto
class ProjectHistory(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="history")
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(verbose_name="Alterações")

    def __str__(self):
        return f"Histórico de {self.project.credit_line.name} - {self.project.client.name} em {self.timestamp}"

# Documentos do projeto
class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_documents')
    file = models.FileField(upload_to=project_document_directory_path, verbose_name="Documento")
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=100, verbose_name="Tipo de Arquivo")
    file_size = models.IntegerField(verbose_name="Tamanho do Arquivo (bytes)")

    def __str__(self):
        return f"Documento de {self.project.credit_line.name} - {self.project.client.name} - {self.file_name}"

    def delete(self, *args, **kwargs):
        if self.file:
            try:
                # Tentar deletar o arquivo do storage (funciona tanto local quanto S3)
                self.file.delete(save=False)
            except Exception:
                # Se falhar, continua com a exclusão do registro no banco
                pass
        super().delete(*args, **kwargs)
