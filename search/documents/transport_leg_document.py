# search/documents/transport_leg_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from logistics.models.transport_leg import TransportLeg
from logistics.models.shipment import Shipment
from logistics.models.transport_provider import TransportProvider


@registry.register_document


class TransportLegDocument(Document):
    shipment = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'total_cost': fields.FloatField(),
    })

    provider = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'license_number': fields.TextField(),
    })

    origin_coords = fields.GeoPointField()
    destination_coords = fields.GeoPointField()
    current_location = fields.GeoPointField()

    class Index:
        name = 'transport_legs'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = TransportLeg
        fields = [
            'sequence_number',
            'origin_name',
            'destination_name',
            'mode',
            'status',
            'scheduled_start',
            'scheduled_end',
            'actual_start',
            'actual_end',
            'last_tracked_at',
            'base_fare',
            'distance_fee',
            'tax',
            'jamiikazini_commission',
            'total_cost',
            # 'metadata',  ← ONDOA hii line
            'created_at',
            'updated_at',
        ]

        related_models = [Shipment, TransportProvider]

    def get_queryset(self):
        return super().get_queryset().select_related('shipment', 'provider')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Shipment):
            return related_instance.legs.all()
        if isinstance(related_instance, TransportProvider):
            return related_instance.legs.all()