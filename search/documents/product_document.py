# search/documents/product_document.py

from django.conf import settings

# Only import and register if Elasticsearch is enabled
if not settings.DEBUG and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
    
    from django_elasticsearch_dsl import Document, Index, fields
    from django_elasticsearch_dsl.registries import registry
    from businesses.models.product import Product
    from businesses.models.business import Business
    
    # Unda Index ya bidhaa
    product_index = Index('products')
    product_index.settings(
        number_of_shards=1,
        number_of_replicas=0
    )

    @registry.register_document
    class ProductDocument(Document):
        # Business fields
        business_name = fields.TextField(attr='business.name')
        business_id = fields.KeywordField(attr='business.id')
        institution_id = fields.TextField(attr='business.institution.id')
        location = fields.GeoPointField(attr='business.location')

        # Currency - Handle ForeignKey properly
        currency = fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'code': fields.TextField(),
            'symbol': fields.TextField(),
            'name': fields.TextField(),
        })
        
        currency_code = fields.TextField(attr='currency.code')
        currency_symbol = fields.TextField(attr='currency.symbol')

        # Tags prepared separately (ArrayField)
        tags = fields.TextField(multi=True)

        class Index:
            name = 'products'
            settings = {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }

        class Django:
            model = Product
            related_models = [Business]
            fields = [
                'id',
                'name',
                'slug',
                'description',
                'type',
                'price',
                'discount_price',
                'quantity_in_stock',
                'unit',
                'is_available',
                'is_featured',
                'image',
                'additional_images',
                'tax_inclusive',
                'tax_rate',
                'external_link',
                'language_code',
                'created_at',
                'updated_at',
            ]

        def get_queryset(self):
            return super().get_queryset().select_related(
                'business',
                'business__institution',
                'currency'
            )

        def prepare_currency(self, instance):
            """Prepare currency data for Elasticsearch"""
            if instance.currency:
                return {
                    'id': instance.currency.id,
                    'code': instance.currency.code,
                    'symbol': instance.currency.symbol,
                    'name': instance.currency.name,
                }
            return None

        def prepare_tags(self, instance):
            """Prepare tags array for Elasticsearch"""
            if instance.tags:
                return instance.tags
            return []

        def prepare_additional_images(self, instance):
            """Prepare additional images array"""
            if instance.additional_images:
                return instance.additional_images
            return []

        def prepare_location(self, instance):
            """Prepare location from business"""
            if instance.business and instance.business.location:
                return {
                    "lat": instance.business.location.y,
                    "lon": instance.business.location.x,
                }
            return None

        def get_instances_from_related(self, related_instance):
            """Rebuild index when related models change"""
            if isinstance(related_instance, Business):
                return related_instance.products.all()
            return None

else:
    # Development mode - provide dummy ProductDocument
    print("ProductDocument SKIPPED - using dummy (development mode)")
    
    class ProductDocument:
        """Dummy document for development"""
        @classmethod
        def search(cls):
            from businesses.models import Product
            return Product.objects.all()
            
        @classmethod
        def get(cls, id):
            from businesses.models import Product
            return Product.objects.get(id=id)