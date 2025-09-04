from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden


def custom_404_view(request, exception):
    """
    View personalizada para erro 404 - Página não encontrada
    """
    return HttpResponseNotFound(render(request, 'errors/404.html'))


def custom_500_view(request):
    """
    View personalizada para erro 500 - Erro interno do servidor
    """
    return HttpResponseServerError(render(request, 'errors/500.html'))


def custom_403_view(request, exception):
    """
    View personalizada para erro 403 - Acesso negado
    """
    return HttpResponseForbidden(render(request, 'errors/403.html'))
