# jamiitasks/apps.py

from django.apps import AppConfig

class JamiitasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jamiitasks'
    verbose_name = "Jamii Tasks"

    def ready(self):
        import jamiitasks.signals.celery_dlq_handler