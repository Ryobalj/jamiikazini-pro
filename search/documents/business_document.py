# search/documents/business_document.py

from django.conf import settings

# Only import and register if Elasticsearch is enabled
if not settings.DEBUG and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
    
    from django_elasticsearch_dsl import Document, Index, fields
    from django_elasticsearch_dsl.registries import registry
    from businesses.models.business import Business
    
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

        category = fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'slug': fields.TextField(),
            'description': fields.TextField()
        })

        institution = fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
        })

        owner = fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'full_name': fields.TextField(),
            'email': fields.TextField(),
        })

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
                'id': category.id,
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
                    'id': instance.institution.id,
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

else:
    # Development mode - provide dummy BusinessDocument for imports
    print("BusinessDocument SKIPPED - using dummy (development mode)")
    
    class BusinessDocument:
        """Dummy document for development"""
        @classmethod
        def search(cls):
            from businesses.models import Business
            return Business.objects.all()
            
        @classmethod
        def get(cls, id):
            from businesses.models import Business
            return Business.objects.get(id=id)