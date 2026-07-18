# businesses/serializers/product_offer_serializer.py

from rest_framework import serializers

from businesses.models.product_offer import ProductOffer, ProductOfferStatus
from businesses.models.product import Product


class ProductOfferSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True, default=None)
    business_id = serializers.CharField(source="product.business_id", read_only=True, default=None)
    business_name = serializers.CharField(source="product.business.name", read_only=True, default=None)
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True, default=None)
    current_price = serializers.DecimalField(source="product.price", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProductOffer
        fields = [
            "id", "product", "product_name", "business_id", "business_name",
            "buyer", "buyer_name", "quantity", "current_price",
            "proposed_unit_price", "counter_unit_price", "status", "note",
            "consumed", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "buyer", "counter_unit_price", "status", "consumed", "created_at", "updated_at"]

    def validate(self, attrs):
        if self.instance is not None:
            return attrs
        product = attrs["product"]
        if not product.is_available:
            raise serializers.ValidationError({"product": "Bidhaa hii haipatikani kwa sasa."})
        quantity = attrs.get("quantity")
        if quantity is not None and product.quantity_in_stock < quantity:
            raise serializers.ValidationError(
                {"quantity": f"Stock haitoshi kwa '{product.name}' (zilizopo: {product.quantity_in_stock})."}
            )
        proposed = attrs.get("proposed_unit_price")
        if proposed is not None and proposed <= 0:
            raise serializers.ValidationError({"proposed_unit_price": "Bei iliyopendekezwa lazima iwe zaidi ya sifuri."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["buyer"] = request.user
        return super().create(validated_data)


class ProductOfferRespondSerializer(serializers.Serializer):
    """decision: ACCEPT | REJECT | COUNTER. counter_unit_price required only for COUNTER."""
    decision = serializers.ChoiceField(choices=["ACCEPT", "REJECT", "COUNTER"])
    counter_unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    def validate(self, attrs):
        if attrs["decision"] == "COUNTER" and not attrs.get("counter_unit_price"):
            raise serializers.ValidationError({"counter_unit_price": "Weka bei mbadala."})
        if attrs.get("counter_unit_price") is not None and attrs["counter_unit_price"] <= 0:
            raise serializers.ValidationError({"counter_unit_price": "Bei mbadala lazima iwe zaidi ya sifuri."})
        return attrs


class ProductOfferBuyerDecisionSerializer(serializers.Serializer):
    """decision: ACCEPT | REJECT - buyer's response to a seller's counter-offer."""
    decision = serializers.ChoiceField(choices=["ACCEPT", "REJECT"])
