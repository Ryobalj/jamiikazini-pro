# search/documents/service_document.py

from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from businesses.models.service import Service
from businesses.models.category import BusinessCategory

service_index = Index('services')
service_index.settings(number_of_shards=1, number_of_replicas=0)

@registry.register_document
class ServiceDocument(Document):
    business = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
        'is_active': fields.BooleanField(),
    })

    location = fields.GeoPointField(attr='business.location')  # Added for location-based search
    institution_id = fields.IntegerField(attr='business.institution_id')  # Optional: useful for access control

    category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'slug': fields.TextField(),
        'description': fields.TextField()
    })

    class Index:
        name = 'services'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'price',
            'billing_type',
            'location_type',
            'requires_booking',
            'is_available',
            'duration_minutes',
        ]
        related_models = [Service.business.field.related_model]

    def get_queryset(self):
        return super().get_queryset().select_related('business')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Service.business.field.related_model):
            return related_instance.services.all()