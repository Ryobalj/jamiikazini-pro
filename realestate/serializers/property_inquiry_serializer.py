# realestate/serializers/property_inquiry_serializer.py

from rest_framework import serializers

from realestate.models.property_inquiry import PropertyInquiry


class PropertyInquirySerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True)
    property_address = serializers.CharField(source="property.address_text", read_only=True)
    property_owner_name = serializers.CharField(source="property.owner.name", read_only=True)
    reservation_amount = serializers.DecimalField(
        source="property.reservation_amount", max_digits=14, decimal_places=2, read_only=True,
    )

    class Meta:
        model = PropertyInquiry
        fields = [
            "id", "property", "property_address", "property_owner_name", "buyer", "buyer_name",
            "message", "status", "reservation_amount", "reserved_at", "buyer_confirmed_at",
            "owner_confirmed_at", "completed_at", "cancelled_at", "created_at",
        ]
        read_only_fields = fields


class PropertyInquiryCreateSerializer(serializers.Serializer):
    property = serializers.UUIDField()
    message = serializers.CharField(required=False, allow_blank=True, default="")
