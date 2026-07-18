# search/documents/transport_provider_document.py

from django.conf import settings
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

    # Institution is UUID-keyed - KeywordField, not IntegerField.
    institution = fields.ObjectField(properties={
        'id': fields.KeywordField(),
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

    def prepare_institution(self, instance):
        institution = instance.institution
        if not institution:
            return None
        return {'id': str(institution.id), 'name': institution.name}

    def prepare_location(self, instance):
        if instance.location:
            return {"lat": instance.location.y, "lon": instance.location.x}
        return None

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.transport_providers.all()
        if isinstance(related_instance, Institution):
            return related_instance.transport_providers.all()

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                TransportProvider.objects.filter(is_approved=True).select_related("user", "institution"),
                search_fields=("provider_type",),
            )
        return super().search(using=using, index=index, **kwargs)
