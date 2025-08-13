from django.apps import AppConfig

class EnterprisesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "enterprises"

    def ready(self):
        import enterprises.signals  # Importar signals quando app estiver pronto