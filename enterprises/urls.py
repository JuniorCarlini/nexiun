from . import views
from django.urls import path

urlpatterns = [
    path('create-enterprise/', views.create_enterprise, name='create_enterprise'),
    path('register_client/', views.register_client_view, name='register_client'),
    path('view-client/<int:client_id>/', views.view_client_view, name='view_client'),
    path('toggle-client-status/<int:client_id>/', views.toggle_client_status_view, name='toggle_client_status'),
    path('project-client/<int:project_id>/', views.client_project_details_view, name='details_project_client'),
    path('list_clients/', views.client_list_view, name='list_clients'),

    # Messages
    path('list-messages/', views.list_messages_view, name='list_messages'),
    path('edit-message/<int:message_id>/', views.edit_message_view, name='edit_message'),
    path('new-message/', views.new_message_view, name='new_message'),
    
    # Test
    path('test-redirect/', views.test_redirect_view, name='test_redirect'),
]
