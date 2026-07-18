# search/apps.py

from django.apps import AppConfig
from django.conf import settings

DOCUMENT_MODULES = [
    "search.documents.business_document",
    "search.documents.product_document",
    "search.documents.branch_document",
    "search.documents.department_document",
    "search.documents.driver_document",
    "search.documents.review_document",
    "search.documents.service_document",
    "search.documents.shipment_document",
    "search.documents.staff_profile_document",
    "search.documents.syllabus_document",
    "search.documents.transport_leg_document",
    "search.documents.transport_provider_document",
    "search.documents.transport_provider_verification_document",
]


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
    verbose_name = "Search"

    def ready(self):
        # Document classes are now always importable (each one gates its own
        # Document.search() behavior on ELASTICSEARCH_ENABLED internally via
        # search.utils.db_fallback.DBFallbackSearch), so registration is safe
        # in every environment - django_elasticsearch_dsl's registry is a pure
        # in-memory mapping and ELASTICSEARCH_DSL_AUTOSYNC=False (dev settings)
        # means no signal ever tries to actually reach a cluster.
        import importlib
        for module_path in DOCUMENT_MODULES:
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                print(f"Failed to load search document module {module_path}: {e}")

        if not settings.DEBUG and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            print("Search documents LOADED (production mode)")
        else:
            print("Search documents LOADED with DB fallback (development mode)")
