from .models import Enterprise
from django.http import Http404
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404

class SubdomainMiddleware:
    """
    Middleware para detectar subdomínios e configurar a empresa correta
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Detecta o subdomínio da requisição
        host = request.get_host().lower()
        
        # Remove porta se presente (para desenvolvimento)
        if ':' in host:
            host = host.split(':')[0]
        
        # Verifica se é um subdomínio do nexiun.com.br
        if host.endswith('.nexiun.com.br'):
            subdomain = host.replace('.nexiun.com.br', '')
            
            # Busca a empresa pelo subdomínio
            try:
                enterprise = Enterprise.objects.get(subdomain=subdomain)
                request.current_enterprise = enterprise
            except Enterprise.DoesNotExist:
                # Subdomínio não encontrado - retorna 404
                raise Http404(f"Empresa com subdomínio '{subdomain}' não encontrada.")
        
        # Suporte para desenvolvimento local com .nexiun.local
        elif host.endswith('.nexiun.local'):
            subdomain = host.replace('.nexiun.local', '')
            
            # Busca a empresa pelo subdomínio
            try:
                enterprise = Enterprise.objects.get(subdomain=subdomain)
                request.current_enterprise = enterprise
            except Enterprise.DoesNotExist:
                # Subdomínio não encontrado - retorna 404
                raise Http404(f"Empresa com subdomínio '{subdomain}' não encontrada.")
        
        elif host in ['nexiun.com.br', 'www.nexiun.com.br', 'nexiun.local', 'localhost', '127.0.0.1']:
            # Domínio principal - modo multi-tenant tradicional
            request.current_enterprise = None
        
        elif settings.DEBUG and (host.startswith('localhost') or host.startswith('127.0.0.1')):
            # Desenvolvimento local - permite qualquer host
            request.current_enterprise = None
        
        else:
            # Host não reconhecido
            if not settings.DEBUG:
                raise Http404("Domínio não reconhecido.")
            request.current_enterprise = None

        response = self.get_response(request)
        return response

class EnterpriseRequiredMiddleware:
    """
    Middleware para verificar se o usuário possui uma empresa vinculada
    Agora considera o contexto de subdomínio
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que não precisam de verificação de empresa
        exempt_paths = [
            '/users/login/',
            '/logout/', 
            '/enterprises/create-enterprise/', 
            '/admin/',
            '/password-reset/',
            '/password-reset/done/',
            '/password-reset-confirm/',
            '/password-reset-complete/',
        ]
        
        # Verifica se a URL atual está isenta
        if any(request.path.startswith(path) for path in exempt_paths):
            response = self.get_response(request)
            return response
        
        # Se o usuário está autenticado
        if request.user.is_authenticated:
            # Se estamos em um subdomínio específico
            if hasattr(request, 'current_enterprise') and request.current_enterprise:
                # Verifica se o usuário pertence a esta empresa
                if request.user.enterprise != request.current_enterprise:
                    # Usuário não pertence a esta empresa - faz logout e redireciona para login
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('login')
            
            # Se não estamos em subdomínio específico e usuário não tem empresa
            elif not hasattr(request, 'current_enterprise') or request.current_enterprise is None:
                if request.user.enterprise is None:
                    # Redireciona para criar empresa
                    return redirect('create_enterprise')

        response = self.get_response(request)
        return response
