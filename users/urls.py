from . import views
from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),

    # Configurações
    path('config/', views.config_view, name='config'),

    # Usuários
    path('create-user/', views.create_user_view, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('list-users/', views.list_users_view, name='list_users'),
]
