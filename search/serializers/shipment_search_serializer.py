# search/serializers/shipment_search_serializer.py

from rest_framework import serializers


class ProductESSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()


class UserESSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class TransportProviderESSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    provider_type = serializers.CharField()


class ShipmentSearchSerializer(serializers.Serializer):
    id = serializers.CharField()  # Elasticsearch returns string IDs
    product = ProductESSerializer()
    sender = UserESSerializer()
    receiver = UserESSerializer()
    transport_providers = TransportProviderESSerializer(many=True)
    preferred_transport_modes = serializers.ListField(child=serializers.CharField())

    origin = serializers.DictField(child=serializers.FloatField())
    destination = serializers.DictField(child=serializers.FloatField(), allow_null=True)

    status = serializers.CharField()
    tax_paid = serializers.FloatField()
    jamiikazini_commission = serializers.FloatField()
    transport_fee = serializers.FloatField()
    total_cost = serializers.FloatField()
    institution_id = serializers.IntegerField(allow_null=True)

    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()