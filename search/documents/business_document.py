# search/documents/business_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from businesses.models.business import Business

# Registering here (and always defining the Document class below) is safe even
# when Elasticsearch is disabled - django_elasticsearch_dsl's registry is a
# pure in-memory mapping and ELASTICSEARCH_DSL_AUTOSYNC=False (dev settings)
# means no signal ever tries to actually reach a cluster. Only Document.search()
# below is gated - it returns a Postgres-backed fallback when ES is off.
business_index = Index('businesses')
business_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@registry.register_document
class BusinessDocument(Document):
    location = fields.GeoPointField()

    phone = fields.TextField(
        attr='phone.as_e164',
        fields={'raw': fields.KeywordField()}
    )

    # id fields use KeywordField (not IntegerField) below because Business,
    # BusinessCategory and Institution are all UUID-keyed models.
    category = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
        'slug': fields.TextField(),
        'description': fields.TextField()
    })

    institution = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })
    institution_id = fields.KeywordField(attr='institution.id')

    owner = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'full_name': fields.TextField(),
        'email': fields.TextField(),
    })
    owner_id = fields.IntegerField(attr='owner.id')

    class Index:
        name = 'businesses'

    class Django:
        model = Business
        fields = [
            'id',
            'name',
            'description',
            'email',
            'website',
            'is_active',
        ]

    def prepare_category(self, instance):
        category = instance.category
        if not category:
            return None
        return {
            'id': str(category.id),
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
        }

    def prepare_location(self, instance):
        if instance.location:
            return {
                "lat": instance.location.y,
                "lon": instance.location.x,
            }
        return None

    def prepare_institution(self, instance):
        if instance.institution:
            return {
                'id': str(instance.institution.id),
                'name': instance.institution.name,
            }
        return None

    def prepare_owner(self, instance):
        if instance.owner:
            return {
                'id': instance.owner.id,
                'full_name': instance.owner.full_name,
                'email': instance.owner.email,
            }
        return None

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                Business.objects.filter(is_active=True).select_related("category", "institution", "owner"),
                search_fields=("name", "description", "category__name"),
            )
        return super().search(using=using, index=index, **kwargs)
