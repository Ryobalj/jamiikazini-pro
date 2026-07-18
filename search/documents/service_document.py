# search/documents/service_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from businesses.models.service import Service
from businesses.models.category import BusinessCategory

service_index = Index('services')
service_index.settings(number_of_shards=1, number_of_replicas=0)

@registry.register_document
class ServiceDocument(Document):
    # Business/BusinessCategory/Institution are UUID-keyed - KeywordField/TextField,
    # not IntegerField.
    business = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
        'is_active': fields.BooleanField(),
    })

    location = fields.GeoPointField()
    institution_id = fields.KeywordField(attr='business.institution_id')

    category = fields.ObjectField(properties={
        'id': fields.KeywordField(),
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
            'created_at',
        ]
        related_models = [Service.business.field.related_model]

    def get_queryset(self):
        return super().get_queryset().select_related('business', 'category')

    def prepare_location(self, instance):
        if instance.business and instance.business.location:
            return {
                "lat": instance.business.location.y,
                "lon": instance.business.location.x,
            }
        return None

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Service.business.field.related_model):
            return related_instance.services.all()

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                Service.objects.filter(is_available=True).select_related("business", "category"),
                search_fields=("name", "description", "category__name"),
            )
        return super().search(using=using, index=index, **kwargs)
