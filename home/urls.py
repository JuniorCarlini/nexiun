from . import views
from django.urls import path

urlpatterns = [
    # Views de páginas
    path('', views.home, name='home'),
]