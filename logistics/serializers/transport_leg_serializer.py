# logistics/serializers/transport_leg_serializer.py

from rest_framework import serializers
from logistics.models import TransportLeg, LegStatusLog
from kiini.helpers.domain import generate_subdomain_url
from logistics.serializers.geo_fields import PointJSONField


class LegStatusLogSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LegStatusLog
        fields = ['id', 'status', 'remarks', 'updated_by', 'timestamp']


class TransportLegSerializer(serializers.ModelSerializer):
    status_logs = LegStatusLogSerializer(many=True, read_only=True)
    origin_coords = PointJSONField(required=False, allow_null=True)
    destination_coords = PointJSONField(required=False, allow_null=True)
    current_location = PointJSONField(required=False, allow_null=True)
    shipment_tracking_url = serializers.SerializerMethodField()
    provider_dashboard_url = serializers.SerializerMethodField()
    receiver_view_url = serializers.SerializerMethodField()

    class Meta:
        model = TransportLeg
        fields = [
            'id', 'shipment', 'shipment_tracking_url', 'provider_dashboard_url', 'receiver_view_url',
            'provider', 'sequence_number',
            'origin_name', 'origin_coords', 'destination_name', 'destination_coords',
            'mode', 'status', 'scheduled_start', 'scheduled_end',
            'actual_start', 'actual_end', 'current_location', 'last_tracked_at',
            'base_fare', 'distance_fee', 'tax', 'jamiikazini_commission', 'total_cost',
            'metadata', 'created_at', 'updated_at', 'status_logs'
        ]

    def get_shipment_tracking_url(self, obj):
        sender = getattr(obj.shipment, 'sender', None)
        institution = getattr(sender, 'institution', None)
        if institution and institution.domain:
            return generate_subdomain_url(institution.domain, f"/track/shipment/{obj.shipment.id}/")
        return None

    def get_provider_dashboard_url(self, obj):
        provider = getattr(obj, 'provider', None)
        user = getattr(provider, 'user', None)
        institution = getattr(user, 'institution', None)
        if institution and institution.domain:
            return generate_subdomain_url(institution.domain, f"/dashboard/shipments/{obj.shipment.id}/")
        return None

    def get_receiver_view_url(self, obj):
        receiver = getattr(obj.shipment, 'receiver', None)
        institution = getattr(receiver, 'institution', None)
        if institution and institution.domain:
            return generate_subdomain_url(institution.domain, f"/view/shipment/{obj.shipment.id}/")
        return None