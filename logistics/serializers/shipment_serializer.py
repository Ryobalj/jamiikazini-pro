# logistics/serializers/shipment_serializer.py

from rest_framework import serializers
from logistics.models import Shipment, TransportProvider
from accounts.models import User
from businesses.models.product import Product
from accounts.serializers import UserMinimalSerializer
from businesses.serializers.product_serializer import ProductMinimalSerializer


class TransportProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportProvider
        fields = ['id', 'name', 'contact_info']  # add more fields as needed


class ShipmentSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)
    receiver = UserMinimalSerializer(read_only=True)
    product = ProductMinimalSerializer(read_only=True)

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='receiver', write_only=True
    )
    transport_providers = TransportProviderSerializer(many=True, read_only=True)
    transport_providers_ids = serializers.PrimaryKeyRelatedField(
        queryset=TransportProvider.objects.all(),
        many=True,
        source='transport_providers',
        write_only=True
    )

    class Meta:
        model = Shipment
        fields = [
            'id', 'product', 'product_id', 'sender', 'receiver', 'receiver_id',
            'preferred_transport_modes', 'route_details',
            'transport_providers', 'transport_providers_ids',
            'status', 'tax_paid', 'jamiikazini_commission',
            'transport_fee', 'total_cost',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)