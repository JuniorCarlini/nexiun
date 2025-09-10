from . import views
from django.urls import path

urlpatterns = [
    # URLs das Unidades
    path('create-unit/', views.create_unit_view, name='create_unit'),
    path('edit-unit/<int:unit_id>/', views.units_edit_view, name='edit_unit'),
    path('toggle-unit-status/<int:unit_id>/', views.toggle_unit_status_view, name='toggle_unit_status'),
    path('units-list/', views.units_list_view, name='units_list'),
    
    # URLs das Contas Bancárias
    path('create-bank-account/', views.create_bank_account_view, name='create_bank_account'),
    path('edit-bank-account/<int:account_id>/', views.edit_bank_account_view, name='edit_bank_account'),
    path('toggle-bank-account-status/<int:account_id>/', views.toggle_bank_account_status_view, name='toggle_bank_account_status'),
    
    # URLs do Sistema Financeiro das Unidades
    path('dashboard-financeiro/', views.financial_dashboard_new_view, name='dashboard_financeiro'),
    path('transactions/', views.unit_transactions_list_view, name='unit_transactions_list'),
    path('transactions/unit/<int:unit_id>/', views.unit_transactions_list_view, name='unit_transactions_list'),
    path('add-transaction/', views.add_transaction_view, name='add_transaction'),
    path('edit-transaction/<int:transaction_id>/', views.edit_transaction_view, name='edit_transaction'),
    path('delete-transaction/<int:transaction_id>/', views.delete_transaction_view, name='delete_transaction'),
]
