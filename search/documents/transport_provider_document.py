# search/documents/transport_provider_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from logistics.models.transport_provider import TransportProvider
from accounts.models import User
from kiini.models.institution import Institution


@registry.register_document
class TransportProviderDocument(Document):
    user = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'username': fields.TextField(),
        'email': fields.TextField(),
    })

    institution = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    location = fields.GeoPointField()

    class Index:
        name = 'transport_providers'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = TransportProvider
        fields = [
            'provider_type',
            'is_approved',
            'created_at',
            'updated_at',
        ]
        related_models = [User, Institution]

    def get_queryset(self):
        return super().get_queryset().select_related('user', 'institution')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.transport_providers.all()
        if isinstance(related_instance, Institution):
            return related_instance.transport_providers.all()