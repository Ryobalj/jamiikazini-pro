# search/documents/shipment_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from logistics.models.shipment import Shipment
from logistics.models.transport_provider import TransportProvider
from accounts.models import User
from businesses.models.product import Product


@registry.register_document
class ShipmentDocument(Document):
    product = fields.ObjectField(properties={
        'id': fields.IntegerField(),
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

    transport_providers = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'provider_type': fields.TextField(),
    })

    preferred_transport_modes = fields.KeywordField(multi=True)

    # Location-based search field (assuming route_details has origin as point)
    origin = fields.GeoPointField(attr='route_details.origin')  # Needs to be a PointField in model
    destination = fields.GeoPointField(attr='route_details.destination', null=True)

    # Optional: for internal access filtering
    institution_id = fields.IntegerField(attr='institution_id', null=True)

    class Index:
        name = 'shipments'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Shipment
        fields = [
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
        ).prefetch_related('transport_providers')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Product):
            return related_instance.shipments.all()
        if isinstance(related_instance, User):
            return related_instance.sent_shipments.all() | related_instance.received_shipments.all()
        if isinstance(related_instance, TransportProvider):
            return related_instance.shipments.all()