# agriculture/serializers/harvest_contract_serializer.py

from decimal import Decimal
from rest_framework import serializers

from agriculture.models.harvest_contract import HarvestContract


class HarvestContractSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True)
    seller_name = serializers.CharField(source="seller.name", read_only=True, default=None)
    estimated_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    deposit_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = HarvestContract
        fields = [
            "id", "buyer", "buyer_name", "seller", "seller_name", "crop_description",
            "estimated_weight_kg", "agreed_price_per_kg", "estimated_total", "deposit_amount",
            "delivery_window_start", "delivery_window_end", "status",
            "buyer_confirmed_weight", "buyer_confirmed_at",
            "seller_confirmed_weight", "seller_confirmed_at",
            "settled_at", "cancelled_at", "created_at",
        ]
        read_only_fields = fields


class HarvestContractCreateSerializer(serializers.Serializer):
    crop_description = serializers.CharField(max_length=255)
    estimated_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    agreed_price_per_kg = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    delivery_window_start = serializers.DateField()
    delivery_window_end = serializers.DateField()

    def validate(self, attrs):
        if attrs["delivery_window_end"] < attrs["delivery_window_start"]:
            raise serializers.ValidationError({"delivery_window_end": "Lazima iwe baada ya delivery_window_start."})
        return attrs


class HarvestContractClaimSerializer(serializers.Serializer):
    business_id = serializers.UUIDField()


class HarvestContractDeliverySerializer(serializers.Serializer):
    delivered_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
