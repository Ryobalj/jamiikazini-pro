# search/serializers/shipment_search_serializer.py

from rest_framework import serializers


class ProductESSerializer(serializers.Serializer):
    id = serializers.CharField()  # Product is UUID-keyed, not an integer PK
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class UserESSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class TransportProviderESSerializer(serializers.Serializer):
    id = serializers.CharField()  # TransportProvider is UUID-keyed, not an integer PK
    name = serializers.CharField()
    provider_type = serializers.CharField(required=False, allow_null=True)


class ShipmentSearchSerializer(serializers.Serializer):
    id = serializers.CharField()  # Elasticsearch returns string IDs
    product = ProductESSerializer(required=False, allow_null=True)
    sender = UserESSerializer(required=False, allow_null=True)
    receiver = UserESSerializer(required=False, allow_null=True)
    transport_providers = TransportProviderESSerializer(many=True, required=False)
    preferred_transport_modes = serializers.ListField(child=serializers.CharField(), required=False)

    origin = serializers.DictField(child=serializers.FloatField(), required=False, allow_null=True)
    destination = serializers.DictField(child=serializers.FloatField(), allow_null=True, required=False)

    status = serializers.CharField()
    tax_paid = serializers.FloatField()
    jamiikazini_commission = serializers.FloatField()
    transport_fee = serializers.FloatField()
    total_cost = serializers.FloatField()

    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()