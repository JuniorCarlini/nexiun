import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool)

# Configuração de hosts permitidos - agora vem do .env
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# CSRF Trusted Origins - agora vem do .env  
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    'home.apps.HomeConfig',
    
    # Third party apps
    'storages',

    # Aplicações do projeto
    "users",
    "units",
    "projects",
    "enterprises",
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "enterprises.middleware.SubdomainMiddleware",  # Detecta subdomínios
    "enterprises.middleware.EnterpriseRequiredMiddleware",
    "projects.middleware.CurrentUserMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "enterprises.context_processors.custom_context",
                "core.context_processors.user_units_context",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Configuração do banco de dados - PostgreSQL para produção, SQLite para desenvolvimento
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
                    'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
            'OPTIONS': {
                # Configuração para psycopg v3
                'application_name': 'nexiun',
            },
        }
    }

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGES = [
    ('pt', 'Portuguese'),
    ('en', 'English'),
]

# Definir o modelo de usuário personalizado
AUTH_USER_MODEL = 'users.User'

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Humanize
USE_THOUSAND_SEPARATOR = True

THOUSAND_SEPARATOR = '.'

DECIMAL_SEPARATOR = ','

NUMBER_GROUPING = 3

# Configurações de arquivos estáticos e mídia
STATICFILES_DIRS = [os.path.join(BASE_DIR, "statics")]

# Configuração do Amazon S3
if not DEBUG:
    # Configurações do AWS S3
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
    
    # Configuração de SEGURANÇA - Sem ACLs (usar bucket policy)
    AWS_DEFAULT_ACL = None  # Não usar ACLs - configurar via bucket policy
    AWS_S3_FILE_OVERWRITE = False  # Não sobrescrever arquivos
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    
    # URLs assinadas para acesso seguro aos arquivos de mídia
    AWS_QUERYSTRING_AUTH = True  # Usar URLs assinadas
    AWS_QUERYSTRING_EXPIRE = 3600  # URLs expiram em 1 hora
    AWS_S3_SIGNATURE_VERSION = 's3v4'  # Versão de assinatura mais segura
    
    # Configuração para arquivos estáticos no S3 (PÚBLICOS) - Django 5.1+
    STORAGES = {
        "default": {
            "BACKEND": "core.storage.PrivateMediaStorage",
        },
        "staticfiles": {
            "BACKEND": "core.storage.PublicStaticStorage",
        },
    }
    STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # Necessário para collectstatic funcionar
    
    # Storage personalizado para diferentes tipos de arquivo
    PRIVATE_FILE_STORAGE = 'core.storage.PrivateMediaStorage'
    SECURE_DOCUMENT_STORAGE = 'core.storage.SecureDocumentStorage'
    
    # IMPORTANTE: Não definir MEDIA_URL para usar URLs assinadas
else:
    # Configuração local para desenvolvimento
    STATIC_URL = "statics/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    MEDIA_URL = "/uploads/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")

# URL para redirecionar o usuário para a página de login
LOGIN_URL = 'login'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

#quantidade de itens por página
ITEMS_PER_PAGE = 20

# Configuração de email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST')
    EMAIL_PORT = config('EMAIL_PORT', cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

MESSAGES_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Configuração de redirecionamento após reset de senha
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'

# Tempo de expiração do token de recuperação de senha (em segundos)
PASSWORD_RESET_TIMEOUT = 1800  # 30 minutos (30 * 60 = 1800 segundos)

# Configurações de segurança para produção
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    # SECURE_SSL_REDIRECT = True  # 🔧 TEMPORARIAMENTE DESABILITADO PARA TESTES
    # SESSION_COOKIE_SECURE = True  # 🔧 TEMPORARIAMENTE DESABILITADO PARA TESTES
    # CSRF_COOKIE_SECURE = True  # 🔧 TEMPORARIAMENTE DESABILITADO PARA TESTES
    
# Configuração do WhiteNoise removida - usando S3 para arquivos estáticos em produção