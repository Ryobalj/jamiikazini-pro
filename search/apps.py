# search/apps.py

from django.apps import AppConfig
from django.conf import settings


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
    verbose_name = "Search"

    def ready(self):
        # Only import documents in production when Elasticsearch is enabled
        if not settings.DEBUG and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            try:
                import search.documents.business_document
                print("Search documents LOADED (production mode)")
            except ImportError as e:
                print(f"Failed to load search documents: {e}")
        else:
            print("Search documents SKIPPED (development mode)")