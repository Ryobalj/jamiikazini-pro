# search/documents/review_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from businesses.models.review import Review

@registry.register_document
class ReviewDocument(Document):
    user = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'username': fields.TextField(),
    })

    business = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })

    product = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })

    service = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })

    class Index:
        name = 'reviews'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Review
        fields = [
            'id',
            'rating',
            'content',
            'is_approved',
            'created_at',
        ]

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                Review.objects.filter(is_approved=True).select_related("user", "business", "product", "service"),
                search_fields=("content",),
            )
        return super().search(using=using, index=index, **kwargs)