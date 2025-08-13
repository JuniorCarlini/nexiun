import uuid
from django.db import models
from units.models import Unit
from django.utils import timezone
from enterprises.models import Enterprise
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Permission

def user_directory_path(instance, filename):
    unique_filename = f"{uuid.uuid4()}.{filename.split('.')[-1]}"
    return f'user_images/{unique_filename}'

class SystemModule(models.Model):
    """Módulos do sistema (Financeiro, Projetos, Usuários, etc.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descrição")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Ícone Bootstrap")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    
    class Meta:
        verbose_name = "Módulo do Sistema"
        verbose_name_plural = "Módulos do Sistema"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Role(models.Model):
    """Cargos/Roles do sistema"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    permissions = models.ManyToManyField(
        Permission, 
        blank=True, 
        verbose_name="Permissões",
        help_text="Permissões padrão deste cargo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, phone=None, password=None, enterprise=None, unit=None, **extra_fields):
        if not email:
            raise ValueError("O campo email é obrigatório")
        email = self.normalize_email(email)
        
        user = self.model(
            email=email,
            name=name,
            phone=phone,
            enterprise=enterprise,
            unit=unit,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone=None, password=None, enterprise=None, unit=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, phone, password, enterprise, unit, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    THEME_CHOICES = [
        ('light', 'Tema Claro'),
        ('dark', 'Tema Escuro'),
        ('auto', 'Automático (Sistema)'),
    ]
    
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True)
    cpf = models.CharField(max_length=14, unique=True, null=True)
    phone = models.CharField(max_length=20, null=True)
    theme_preference = models.CharField(
        max_length=10, 
        choices=THEME_CHOICES, 
        default='light',
        verbose_name='Preferência de Tema',
        help_text='Escolha o tema de aparência do sistema'
    )
    
    # Sistema de roles e permissions
    roles = models.ManyToManyField(
        Role, 
        blank=True, 
        related_name="users",
        verbose_name="Cargos",
        help_text="Cargos atribuídos ao usuário"
    )
    custom_permissions = models.ManyToManyField(
        Permission, 
        blank=True, 
        related_name="users_with_custom_permission",
        verbose_name="Permissões Customizadas",
        help_text="Permissões específicas além das do cargo"
    )
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    profile_image = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email
    
    def get_all_permissions(self, obj=None):
        """Retorna todas as permissões do usuário (roles + customizadas + padrão Django)"""
        permissions = set(super().get_all_permissions(obj))
        
        # Adiciona permissões dos roles
        for role in self.roles.filter(is_active=True):
            for perm in role.permissions.all():
                permissions.add(f"{perm.content_type.app_label}.{perm.codename}")
        
        # Adiciona permissões customizadas
        for perm in self.custom_permissions.all():
            permissions.add(f"{perm.content_type.app_label}.{perm.codename}")
            
        return permissions
    
    def has_perm(self, perm, obj=None):
        """
        Sobrescreve o método has_perm para incluir permissões dos roles
        """
        # Primeiro verifica com o método padrão Django
        if super().has_perm(perm, obj):
            return True
            
        # Se não tem pelo Django padrão, verifica nos roles
        if not self.is_active:
            return False
            
        # Verifica se tem a permissão nos roles
        for role in self.roles.filter(is_active=True):
            for permission in role.permissions.all():
                if f"{permission.content_type.app_label}.{permission.codename}" == perm:
                    return True
        
        # Verifica se tem a permissão nas customizadas
        for permission in self.custom_permissions.all():
            if f"{permission.content_type.app_label}.{permission.codename}" == perm:
                return True
                
        return False
    
    def has_module_permission(self, module_code, action):
        """Verifica se o usuário tem permissão para uma ação em um módulo específico"""
        perm_name = f"users.{action}_{module_code}"
        return self.has_perm(perm_name)
