# search/documents/branch_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from businesses.models.branch import Branch

@registry.register_document
class BranchDocument(Document):
    business = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })

    services = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })

    location = fields.GeoPointField()

    class Index:
        name = 'branches'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Branch
        fields = [
            'id',
            'name',
            'description',
            'phone',
            'email',
            'is_active',
            'created_at',
        ]

    def prepare_location(self, instance):
        if instance.location:
            return {
                "lat": instance.location.y,
                "lon": instance.location.x,
            }
        return None

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                Branch.objects.filter(is_active=True).select_related("business"),
                search_fields=("name", "description"),
            )
        return super().search(using=using, index=index, **kwargs)