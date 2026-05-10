# jamiiwallet/apps.py

from django.apps import AppConfig

class JamiiwalletConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jamiiwallet'

    def ready(self):
        import jamiiwallet.signals
