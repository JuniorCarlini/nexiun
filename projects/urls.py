from . import views
from django.urls import path

urlpatterns = [
    # Projetos
    path('projects-list/', views.projects_list_view, name='projects_list'),
    path('project-details/<int:project_id>/', views.project_details_view, name='project_details'),
    path('create-project/', views.create_project_view, name='create_project'),

    # Esteira de projetos e pagamentos
    path('conveyor/', views.conveyor_projects_view, name='conveyor_projects'),
    path('conveyor-payments/', views.conveyor_payments_view, name='conveyor_payments'),
    path('conveyor-confirm-payments/', views.conveyor_confirm_payments_view, name='conveyor_confirm_payments'),
    path('conveyor/<int:project_id>/', views.conveyor_project_details_view, name='conveyor_project_details'),
    path('assign-manager/<int:project_id>/', views.assign_manager_view, name='assign_manager'),

    # Bancos
    path('banks-list/', views.banks_list_view, name='banks_list'),
    path('bank-edit/<int:bank_id>/', views.bank_edit_view, name='bank_edit'),
    path('bank-add/', views.add_bank_view, name='bank_add'),
    path('toggle-bank-status/<int:bank_id>/', views.toggle_bank_status_view, name='toggle_bank_status'),

    # Linhas de crédito
    path('credit-line-list/', views.credit_lines_list_view, name='credit_line_list'),
    path('credit-line-edit/<int:credit_line_id>/', views.credit_line_edit_view, name='credit_line_edit'),
    path('credit-line-add/', views.add_credit_line_view, name='credit_line_add'),
    path('toggle-credit-line-status/<int:credit_line_id>/', views.toggle_credit_line_status_view, name='toggle_credit_line_status'),
]
