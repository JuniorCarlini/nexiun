import os
import re
import uuid
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError

def enterprise_directory_path(instance, filename):
    unique_filename = f"{uuid.uuid4()}.{filename.split('.')[-1]}"
    return f'enterprise_images/{unique_filename}'

def client_document_directory_path(instance, filename):
    unique_filename = f"{uuid.uuid4()}.{filename.split('.')[-1]}"
    return f'client_documents/{instance.client.enterprise.id}/{instance.client.id}/{unique_filename}'

def validate_subdomain(value):
    """Valida se o subdomínio está no formato correto"""
    if not value:
        return
    
    # Regex para validar subdomínio: letras, números e hífen, 3-63 caracteres
    if not re.match(r'^[a-z0-9]([a-z0-9\-]{1,61}[a-z0-9])?$', value):
        raise ValidationError(
            'Subdomínio deve conter apenas letras minúsculas, números e hífens. '
            'Deve ter entre 3 e 63 caracteres e não pode começar ou terminar com hífen.'
        )
    
    # Lista de subdomínios reservados
    reserved_subdomains = [
        'www', 'admin', 'api', 'app', 'mail', 'email', 'ftp', 'blog',
        'help', 'support', 'docs', 'dev', 'test', 'staging', 'prod',
        'nexiun', 'sistema', 'painel', 'dashboard', 'login'
    ]
    
    if value.lower() in reserved_subdomains:
        raise ValidationError(f'O subdomínio "{value}" está reservado e não pode ser usado.')

class Enterprise(models.Model):
    name = models.CharField(max_length=255)
    cnpj_or_cpf = models.CharField(max_length=18)
    
    # Campo para subdomínio
    subdomain = models.CharField(
        max_length=63, 
        unique=True, 
        validators=[validate_subdomain],
        help_text='Subdomínio único para acesso (ex: saldus.nexiun.com.br)',
        verbose_name='Subdomínio'
    )
    
    logo_light = models.ImageField(
        upload_to=enterprise_directory_path,
        blank=True,
        default='icons/logo.svg',
        null=True,
        verbose_name='Logo Claro',
        help_text='Logo para usar em fundos claros'
    )
    logo_dark = models.ImageField(
        upload_to=enterprise_directory_path,
        blank=True,
        default='icons/logo_white.svg',
        null=True,
        verbose_name='Logo Escuro',
        help_text='Logo para usar em fundos escuros'
    )
    favicon = models.ImageField(
        upload_to=enterprise_directory_path,
        blank=True,
        default='icons/favicon.svg',
        null=True,
        verbose_name='Favicon',
        help_text='Ícone que aparece na aba do navegador (formato .ico, .png ou .svg)'
    )
    primary_color = models.CharField(max_length=7, default='#05677D')
    secondary_color = models.CharField(max_length=7, default='#FFB845')
    text_icons_color = models.CharField(max_length=7, default='#FFFFFF')
    
    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Gera subdomínio automaticamente se não foi fornecido
        if not self.subdomain:
            self.subdomain = self.generate_subdomain()
        
        # Garante que o subdomínio está em minúsculas
        self.subdomain = self.subdomain.lower()
        
        super().save(*args, **kwargs)
    
    def generate_subdomain(self):
        """Gera um subdomínio baseado no nome da empresa"""
        base_subdomain = slugify(self.name)
        # Remove caracteres especiais e espaços
        base_subdomain = re.sub(r'[^a-z0-9\-]', '', base_subdomain)
        
        # Garante que tenha pelo menos 3 caracteres
        if len(base_subdomain) < 3:
            base_subdomain = f"empresa{base_subdomain}"
        
        # Limita a 50 caracteres para deixar espaço para sufixos
        base_subdomain = base_subdomain[:50]
        
        # Verifica se já existe e adiciona sufixo se necessário
        counter = 1
        subdomain = base_subdomain
        
        while Enterprise.objects.filter(subdomain=subdomain).exists():
            subdomain = f"{base_subdomain}{counter}"
            counter += 1
            
            # Previne loop infinito
            if counter > 9999:
                subdomain = f"{base_subdomain}{uuid.uuid4().hex[:8]}"
                break
        
        return subdomain
    
    def get_full_domain(self):
        """Retorna o domínio completo da empresa"""
        return f"{self.subdomain}.nexiun.com.br"
    
    def get_absolute_url(self):
        """Retorna a URL completa para acessar a empresa"""
        from django.conf import settings
        
        if settings.DEBUG:
            # Em desenvolvimento, usar localhost com porta
            return f"http://{self.subdomain}.nexiun.local:8000"
        else:
            # Em produção, usar domínio real
            return f"https://{self.get_full_domain()}"
    
    def get_logo_url(self, theme='light'):
        """Retorna a URL correta do logo baseado no tema (estático ou upload)"""
        from django.templatetags.static import static
        
        # Seleciona o logo baseado no tema
        logo_field = self.logo_light if theme == 'light' else self.logo_dark
        default_logo = 'icons/logo.svg' if theme == 'light' else 'icons/logo_white.svg'
        
        if not logo_field:
            # Sem logo definido, usar padrão
            return static(default_logo)
        
        # Verifica se é um arquivo de upload real ou o valor padrão
        if str(logo_field) in ['icons/logo.svg', 'icons/logo_white.svg', 'icons/favicon.svg']:
            # É um valor padrão, usar arquivos estáticos
            return static(str(logo_field))
        else:
            # É um arquivo de upload, usar URL de mídia
            return logo_field.url

    def get_logo_light_url(self):
        """Retorna a URL do logo claro"""
        return self.get_logo_url('light')
    
    def get_logo_dark_url(self):
        """Retorna a URL do logo escuro"""
        return self.get_logo_url('dark')
    
    def get_favicon_url(self):
        """Retorna a URL correta do favicon (estático ou upload)"""
        from django.templatetags.static import static
        
        if not self.favicon:
            # Sem favicon definido, usar padrão
            return static('icons/favicon.svg')
        
        # Verifica se é um arquivo de upload real ou o valor padrão
        if str(self.favicon) in ['icons/logo_white.svg', 'icons/favicon.svg']:
            # É um valor padrão, usar arquivos estáticos
            return static(str(self.favicon))
        else:
            # É um arquivo de upload, usar URL de mídia
            return self.favicon.url

class InternalMessage(models.Model):
    SCOPE_CHOICES = [
        ('empresa', 'Toda a Empresa'),
        ('unidade', 'Unidade Específica'),
    ]
    
    title = models.CharField(max_length=255, verbose_name="Título")
    content = models.TextField(verbose_name="Conteúdo")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Data")
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name="Expira em")
    level = models.CharField(max_length=20, choices=[('info', 'Info'), ('warning', 'Aviso'), ('danger', 'Urgente')], default='info', verbose_name="Nível")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="messages", verbose_name="Empresa")
    
    # Novo campo para definir escopo
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='empresa', verbose_name="Escopo")
    unit = models.ForeignKey('units.Unit', on_delete=models.CASCADE, related_name="messages", 
                            null=True, blank=True, verbose_name="Unidade")
    
    class Meta:
        verbose_name = "Mensagem Interna"
        verbose_name_plural = "Mensagens Internas"
        ordering = ['-date']

    def __str__(self):
        scope_text = f" - {self.unit.name}" if self.scope == 'unidade' and self.unit else " - Toda Empresa"
        return f"{self.title}{scope_text}"
    
    def get_scope_display_text(self):
        """Retorna texto amigável para o escopo"""
        if self.scope == 'unidade' and self.unit:
            return f"Unidade: {self.unit.name}"
        return "Toda a Empresa"

CLIENT_STATUS_CHOICES = [
    ('INATIVO', 'Inativo'),
    ('INTERESSADO', 'Interessado'),
    ('EM_NEGOCIACAO', 'Negociação'),
    ('ATIVO', 'Ativo'),
]

# Novas opções para os campos adicionados
PRODUCER_CLASSIFICATION_CHOICES = [
    ('PEQUENO', 'Pequeno Produtor'),
    ('MEDIO', 'Médio Produtor'),
    ('GRANDE', 'Grande Produtor'),
]

ACTIVITY_CHOICES = [
    ('AGRICULTURA', 'Agricultura'),
    ('PECUARIA', 'Pecuária'),
    ('AGRICULTURA/PECUARIA', 'Agricultura/Pecuária'),
    ('OUTROS', 'Outros'),
]

class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF", help_text="CPF do cliente (formato: XXX.XXX.XXX-XX)")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="City")
    observations = models.TextField(blank=True, null=True, verbose_name="Observations")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    
    # Novos campos adicionados
    producer_classification = models.CharField(
        max_length=10,
        choices=PRODUCER_CLASSIFICATION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Enquadramento do Produtor"
    )
    property_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Área Total do Produtor (hectares)",
        help_text="Área total do produtor em hectares"
    )
    activity = models.CharField(
        max_length=25,
        choices=ACTIVITY_CHOICES,
        blank=True,
        null=True,
        verbose_name="Atividade Principal"
    )
    
    status = models.CharField(
        max_length=15, 
        choices=CLIENT_STATUS_CHOICES, 
        default='INATIVO', 
        verbose_name="Situação"
    )
    retorno_ate = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Retorno até",
        help_text="Data de retorno obrigatória quando em negociação"
    )
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="clients", verbose_name="Enterprise")
    units = models.ManyToManyField('units.Unit', blank=True, related_name="clients", verbose_name="Unidades")
    
    # Metadados de auditoria
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_clients', verbose_name='Cadastrado por', null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['name']

    def __str__(self):
        active_status = "Ativo" if self.is_active else "Inativo"
        return f"{self.name} - {self.get_status_display()} ({active_status})"
    
    def get_units_display(self):
        """Retorna uma string com os nomes das unidades do cliente"""
        return ", ".join([unit.name for unit in self.units.all()])
    
    def is_in_unit(self, unit):
        """Verifica se o cliente está vinculado a uma unidade específica"""
        return self.units.filter(id=unit.id).exists()
    
    def get_status_badge_class(self):
        """Retorna a classe CSS para o badge do status"""
        status_classes = {
            'INATIVO': 'bg-secondary',
            'INTERESSADO': 'bg-info',
            'EM_NEGOCIACAO': 'bg-warning text-dark',
            'ATIVO': 'bg-success',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_status_icon(self):
        """Retorna o ícone correspondente ao status"""
        status_icons = {
            'INATIVO': 'fas fa-pause-circle',
            'INTERESSADO': 'fas fa-eye',
            'EM_NEGOCIACAO': 'fas fa-handshake',
            'ATIVO': 'fas fa-check-circle',
        }
        return status_icons.get(self.status, 'fas fa-user')

class ClientDocument(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(
        upload_to=client_document_directory_path,
        verbose_name="Document"
    )
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=100)
    file_size = models.IntegerField()  # Size in bytes

    def __str__(self):
        return f"Document for {self.client.name} - {self.file_name}"

    def delete(self, *args, **kwargs):
        if self.file:
            try:
                # Tentar deletar o arquivo do storage (funciona tanto local quanto S3)
                self.file.delete(save=False)
            except Exception:
                # Se falhar, continua com a exclusão do registro no banco
                pass
        super().delete(*args, **kwargs)

# Histórico de alterações no cliente
class ClientHistory(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="history")
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(verbose_name="Alterações")

    class Meta:
        verbose_name = "Histórico do Cliente"
        verbose_name_plural = "Históricos dos Clientes"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Histórico de {self.client.name} em {self.timestamp}"


# Conta bancária do cliente
class ClientBankAccount(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bank_accounts', verbose_name="Cliente")
    bank = models.ForeignKey('projects.Bank', on_delete=models.CASCADE, verbose_name="Banco")
    agency = models.CharField(max_length=10, verbose_name="Agência", help_text="Número da agência (ex: 1234)")
    account_number = models.CharField(max_length=20, verbose_name="Número da Conta", help_text="Número da conta com dígito (ex: 12345-6)")
    account_type = models.CharField(
        max_length=20,
        choices=[
            ('CORRENTE', 'Conta Corrente'),
            ('POUPANCA', 'Poupança'),
            ('SALARIO', 'Conta Salário'),
        ],
        default='CORRENTE',
        verbose_name="Tipo de Conta"
    )

    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    
    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_bank_accounts', verbose_name='Cadastrado por', null=True, blank=True)

    class Meta:
        verbose_name = "Conta Bancária do Cliente"
        verbose_name_plural = "Contas Bancárias dos Clientes"
        ordering = ['bank__name']
        unique_together = ['client', 'bank', 'agency', 'account_number']  # Evita duplicatas

    def __str__(self):
        status_text = "Ativa" if self.is_active else "Inativa"
        return f"{self.client.name} - {self.bank.name} Ag:{self.agency} Cc:{self.account_number} ({status_text})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def get_formatted_account(self):
        """Retorna a conta formatada: Banco - Ag: XXXX Cc: XXXXX-X"""
        return f"{self.bank.name} - Ag: {self.agency} Cc: {self.account_number}"
    
    def get_account_type_display_short(self):
        """Retorna o tipo de conta de forma abreviada"""
        type_dict = {
            'CORRENTE': 'CC',
            'POUPANCA': 'CP',
            'SALARIO': 'CS',
        }
        return type_dict.get(self.account_type, self.account_type)
