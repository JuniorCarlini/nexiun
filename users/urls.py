from . import views
from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),

    # Configurações
    path('user-config/', views.user_config_view, name='user_config'),
    path('enterprise-config/', views.enterprise_config_view, name='enterprise_config'),

    # Usuários
    path('create-user/', views.create_user_view, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('list-users/', views.list_users_view, name='list_users'),
]
