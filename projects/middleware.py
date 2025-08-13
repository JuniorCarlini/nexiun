from threading import local
from django.utils.deprecation import MiddlewareMixin

_thread_locals = local()

class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Armazena o usuário atual no thread local"""
        _thread_locals.user = getattr(request, 'user', None)

    def process_response(self, request, response):
        """Limpa o usuário atual após a resposta"""
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        return response

def get_current_user():
    """Retorna o usuário atual de forma segura"""
    try:
        return getattr(_thread_locals, 'user', None)
    except AttributeError:
        return None