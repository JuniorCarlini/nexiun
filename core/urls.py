from users import views
from django.conf import settings
from django.contrib import admin
from users.views import logout_view
from django.urls import path, include
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path('logout/', logout_view, name='logout'),
    path("", include("home.urls")),
    path("users/", include("users.urls")),
    path("enterprises/", include("enterprises.urls")),
    path("units/", include("units.urls")),
    path("projects/", include("projects.urls")),
    path('reports/', include('reports.urls')),

    #recuperar senha
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Páginas de erro personalizadas
handler404 = 'core.views.custom_404_view'
handler500 = 'core.views.custom_500_view'
handler403 = 'core.views.custom_403_view'
