from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PrivateMediaStorage(S3Boto3Storage):
    """
    Storage para arquivos de mídia privados no S3
    Gera URLs assinadas que expiram em 1 hora
    """
    location = 'private'  # Pasta no bucket
    default_acl = None  # Não usar ACL - configurar via bucket policy
    file_overwrite = False
    custom_domain = False
    querystring_auth = True
    querystring_expire = 3600  # 1 hora


class PublicStaticStorage(S3Boto3Storage):
    """
    Storage para arquivos estáticos públicos (CSS, JS, imagens do site)
    """
    location = 'static'
    default_acl = None  # Não usar ACL - bucket com configuração de acesso público
    file_overwrite = True
    custom_domain = False
    querystring_auth = False  # Não usar URLs assinadas para arquivos estáticos
    object_parameters = {
        'CacheControl': 'max-age=31536000',  # Cache por 1 ano para arquivos estáticos
    }


class SecureDocumentStorage(S3Boto3Storage):
    """
    Storage para documentos confidenciais
    URLs expiram em 30 minutos para maior segurança
    """
    location = 'documents'
    default_acl = None  # Não usar ACL - configurar via bucket policy
    file_overwrite = False
    custom_domain = False
    querystring_auth = True
    querystring_expire = 1800  # 30 minutos
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        """
        Gera URL assinada com logs de auditoria
        """
        # Para logs de auditoria (opcional)
        if settings.DEBUG:
            print(f"🔐 Gerando URL segura para: {name}")
        
        return super().url(name, parameters, expire or self.querystring_expire, http_method) 