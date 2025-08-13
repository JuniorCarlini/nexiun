import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default="django-insecure--(7^#u%#4e$i62@)ck53t#llolu=7r(p(x6yj0z@rjvhssv=#y")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Configuração de hosts permitidos com suporte a subdomínios
if DEBUG:
    ALLOWED_HOSTS = [
        '*',  # Permite qualquer host em desenvolvimento
        'localhost',
        '127.0.0.1',
        'nexiun.local',
        '*.nexiun.local',
        'nexiun.com.br',
        'www.nexiun.com.br',
        '.nexiun.com.br',  # Para testar produção em debug
    ]
    # CSRF Trusted Origins para desenvolvimento
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://nexiun.local:8000',
        'http://*.nexiun.local:8000',
        'https://nexiun.com.br',
        'https://www.nexiun.com.br',
        'https://*.nexiun.com.br',
    ]
else:
    ALLOWED_HOSTS = [
        'nexiun.com.br',
        'www.nexiun.com.br',
        '.nexiun.com.br',  # Permite todos os subdomínios de nexiun.com.br
    ]
    # CSRF Trusted Origins para produção
    CSRF_TRUSTED_ORIGINS = [
        'https://nexiun.com.br',
        'https://www.nexiun.com.br',
        'https://*.nexiun.com.br',
    ]

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
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
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
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    
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
    EMAIL_HOST = config('EMAIL_HOST', default='localhost')
    EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

MESSAGES_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Configuração de redirecionamento após reset de senha
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'

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