# search/documents/transport_leg_document.py

from django.conf import settings
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

    # TransportProvider is UUID-keyed and has no name/license_number fields of
    # its own (verified against logistics/models/transport_provider.py) -
    # "name" here is the owning user's full_name.
    provider = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
        'provider_type': fields.TextField(),
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
            'id',
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
            # 'metadata',  <- ONDOA hii line
            'created_at',
            'updated_at',
        ]

        related_models = [Shipment, TransportProvider]

    def get_queryset(self):
        return super().get_queryset().select_related('shipment', 'provider', 'provider__user')

    def prepare_provider(self, instance):
        provider = instance.provider
        if not provider:
            return None
        return {
            'id': str(provider.id),
            'name': provider.user.full_name if provider.user else None,
            'provider_type': provider.provider_type,
        }

    def prepare_origin_coords(self, instance):
        return self._point(instance.origin_coords)

    def prepare_destination_coords(self, instance):
        return self._point(instance.destination_coords)

    def prepare_current_location(self, instance):
        return self._point(instance.current_location)

    @staticmethod
    def _point(point):
        if point:
            return {"lat": point.y, "lon": point.x}
        return None

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Shipment):
            return related_instance.legs.all()
        if isinstance(related_instance, TransportProvider):
            return related_instance.legs.all()

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                TransportLeg.objects.select_related("shipment", "provider"),
                search_fields=("origin_name", "destination_name"),
            )
        return super().search(using=using, index=index, **kwargs)
