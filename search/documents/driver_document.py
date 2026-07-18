# search/documents/driver_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from logistics.models.driver import Driver
from logistics.models.transport_provider import TransportProvider

@registry.register_document
class DriverDocument(Document):
    # TransportProvider is UUID-keyed - KeywordField, not IntegerField. It also
    # has no name/license_number fields of its own (verified against
    # logistics/models/transport_provider.py) - "name" here is the owning
    # user's full_name, and provider_type replaces the nonexistent license_number.
    transport_provider = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
        'provider_type': fields.TextField(),
        'institution_id': fields.KeywordField(),
    })

    transport_provider_id = fields.KeywordField()  # For filtering purposes

    class Index:
        name = 'drivers'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Driver
        fields = [
            'id',
            'full_name',
            'license_number',
            'phone_number',
            'is_verified',
            'is_active',
        ]
        related_models = [TransportProvider]

    def get_queryset(self):
        return super().get_queryset().select_related('transport_provider', 'transport_provider__user')

    def prepare_transport_provider(self, instance):
        provider = instance.transport_provider
        if not provider:
            return None
        return {
            'id': str(provider.id),
            'name': provider.user.full_name if provider.user else None,
            'provider_type': provider.provider_type,
            'institution_id': str(provider.institution_id) if provider.institution_id else None,
        }

    def prepare_transport_provider_id(self, instance):
        return str(instance.transport_provider_id) if instance.transport_provider_id else None

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, TransportProvider):
            return related_instance.drivers.all()

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                Driver.objects.filter(is_active=True).select_related("transport_provider"),
                search_fields=("full_name", "license_number"),
            )
        return super().search(using=using, index=index, **kwargs)
