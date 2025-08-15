from . import views
from django.urls import path, include

urlpatterns = [
    # Dashboard Principal
    path('', views.reports_dashboard_view, name='reports_dashboard'),
    
    # Relatórios de Operações
    path('operations/', include([
        path('performance/', views.operations_performance_view, name='operations_performance'),
        path('timing/', views.operations_timing_view, name='operations_timing'),
        path('by-bank/', views.operations_by_bank_view, name='operations_by_bank'),
        path('by-credit-line/', views.operations_by_credit_line_view, name='operations_by_credit_line'),
    ])),
    
    # Relatórios de Clientes
    path('clients/', include([
        path('indicators/', views.clients_indicators_view, name='clients_indicators'),
        path('conversion/', views.clients_conversion_view, name='clients_conversion'),
        path('status-analysis/', views.clients_status_analysis_view, name='clients_status_analysis'),
        path('repurchase/', views.clients_repurchase_view, name='clients_repurchase'),
    ])),
    
    # Relatórios de Desempenho
    path('performance/', include([
        path('captadores/', views.performance_captadores_view, name='performance_captadores'),
        path('projetistas/', views.performance_projetistas_view, name='performance_projetistas'),
        path('unidades/', views.performance_unidades_view, name='performance_unidades'),
        path('bancos/', views.performance_bancos_view, name='performance_bancos'),
        path('carteira/', views.performance_carteira_view, name='performance_carteira'),
    ])),
    
    # Relatórios por Categoria
    path('categories/', include([
        path('client-size/', views.categories_client_size_view, name='categories_client_size'),
        path('operation-type/', views.categories_operation_type_view, name='categories_operation_type'),
        path('by-unit/', views.categories_by_unit_view, name='categories_by_unit'),
        path('comparative/', views.categories_comparative_view, name='categories_comparative'),
    ])),
    
    # Relatórios Especiais
    path('special/', include([
        path('vencimentos/', views.special_vencimentos_view, name='special_vencimentos'),
        path('aniversarios/', views.special_aniversarios_view, name='special_aniversarios'),
        path('carteira-contatos/', views.special_carteira_contatos_view, name='special_carteira_contatos'),
        path('franqueados/', views.special_franqueados_view, name='special_franqueados'),
        path('comissoes/', views.special_comissoes_view, name='special_comissoes'),
    ])),
    
    # Configurações e Utilidades
    path('settings/', views.reports_settings_view, name='reports_settings'),
    path('export/', views.reports_export_view, name='reports_export'),
    
    # APIs para AJAX e gráficos
    path('api/', include([
        path('dashboard-data/', views.api_dashboard_data_view, name='api_dashboard_data'),
        path('operations-chart/', views.api_operations_chart_view, name='api_operations_chart'),
        path('clients-chart/', views.api_clients_chart_view, name='api_clients_chart'),
        path('performance-chart/', views.api_performance_chart_view, name='api_performance_chart'),
        path('refresh-cache/', views.api_refresh_cache_view, name='api_refresh_cache'),
    ])),
] 