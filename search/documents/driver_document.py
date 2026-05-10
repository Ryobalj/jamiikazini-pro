# search/documents/driver_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from logistics.models.driver import Driver
from logistics.models.transport_provider import TransportProvider

@registry.register_document
class DriverDocument(Document):
    transport_provider = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'license_number': fields.TextField(),
        'institution_id': fields.IntegerField()
    })

    transport_provider_id = fields.IntegerField()  # For filtering purposes

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
        return super().get_queryset().select_related('transport_provider')

    def prepare_transport_provider(self, instance):
        provider = instance.transport_provider
        if not provider:
            return None
        return {
            'id': provider.id,
            'name': provider.name,
            'license_number': provider.license_number,
            'institution_id': provider.institution_id,
        }

    def prepare_transport_provider_id(self, instance):
        return instance.transport_provider_id if instance.transport_provider else None

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, TransportProvider):
            return related_instance.drivers.all()