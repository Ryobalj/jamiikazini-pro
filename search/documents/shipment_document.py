# search/documents/shipment_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from logistics.models.shipment import Shipment
from logistics.models.transport_provider import TransportProvider
from accounts.models import User
from businesses.models.product import Product


@registry.register_document
class ShipmentDocument(Document):
    # Product is UUID-keyed - KeywordField, not IntegerField.
    product = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
    })

    sender = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'username': fields.TextField(),
        'email': fields.TextField(),
    })

    receiver = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'username': fields.TextField(),
        'email': fields.TextField(),
    })

    # TransportProvider is UUID-keyed and has no "name" field of its own
    # (verified against logistics/models/transport_provider.py) - "name" here
    # is the owning user's full_name, filled in by prepare_transport_providers.
    transport_providers = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
        'provider_type': fields.TextField(),
    })

    preferred_transport_modes = fields.KeywordField(multi=True)

    # route_details is a schemaless JSONField with no guaranteed origin/destination
    # keys anywhere in the codebase - kept best-effort, may resolve to None.
    origin = fields.GeoPointField(attr='route_details.origin')
    destination = fields.GeoPointField(attr='route_details.destination', null=True)

    # NOTE: Shipment has no institution/institution_id field on the model at
    # all (verified against logistics/models/shipment.py) - a prior
    # institution_id field here was permanently null and has been removed
    # rather than kept as dead data.

    class Index:
        name = 'shipments'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Shipment
        fields = [
            'id',
            'status',
            'tax_paid',
            'jamiikazini_commission',
            'transport_fee',
            'total_cost',
            'created_at',
            'updated_at',
        ]
        related_models = [Product, User, TransportProvider]

    def get_queryset(self):
        return super().get_queryset().select_related(
            'product', 'sender', 'receiver'
        ).prefetch_related('transport_providers', 'transport_providers__user')

    def prepare_transport_providers(self, instance):
        return [
            {
                'id': str(provider.id),
                'name': provider.user.full_name if provider.user else None,
                'provider_type': provider.provider_type,
            }
            for provider in instance.transport_providers.all()
        ]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Product):
            return related_instance.shipments.all()
        if isinstance(related_instance, User):
            return related_instance.sent_shipments.all() | related_instance.received_shipments.all()
        if isinstance(related_instance, TransportProvider):
            return related_instance.shipments.all()

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                Shipment.objects.select_related("product", "sender", "receiver").prefetch_related("transport_providers"),
                search_fields=("product__name", "status"),
            )
        return super().search(using=using, index=index, **kwargs)
