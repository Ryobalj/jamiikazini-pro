from django.apps import AppConfig

class SyllabusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'syllabus'

    def ready(self):
        import syllabus.signals  # Import the signals module

