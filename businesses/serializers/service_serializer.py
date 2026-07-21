# businesses/serializers/service_serializer.py

from rest_framework import serializers
from businesses.models.service import Service, BillingType, ServiceLocationType


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer kwa Model ya Service."""
    name = serializers.CharField(help_text="Jina la huduma.")
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Maelezo mafupi kuhusu huduma hii."
    )
    price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Gharama ya huduma hii."
    )
    billing_type = serializers.ChoiceField(
        choices=BillingType.choices,
        help_text="Aina ya malipo kwa huduma hii (mf. kwa saa, kwa siku)."
    )
    location_type = serializers.ChoiceField(
        choices=ServiceLocationType.choices,
        help_text="Mahali huduma inapopatikana (mf. kwa mtoa huduma, kwa mteja, au mtandaoni)."
    )
    requires_booking = serializers.BooleanField(
        help_text="Inaonesha kama huduma hii inahitaji booking kabla ya kutolewa."
    )
    is_available = serializers.BooleanField(
        help_text="Inaonesha kama huduma hii inapatikana kwa sasa."
    )
    duration_minutes = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Muda unaokadiriwa kwa huduma hii kwa dakika."
    )
    distance = serializers.SerializerMethodField(
        method_name="get_distance",
        help_text="Umbali wa mtumiaji hadi huduma hii (ikiwa imetolewa).",
        read_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "business",
            "category",
            "name",
            "description",
            "price",
            "billing_type",
            "location_type",
            "requires_booking",
            "is_available",
            "duration_minutes",
            "distance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_duration_minutes(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Muda wa huduma lazima uwe zaidi ya sifuri.")
        return value

    def get_distance(self, obj):
        """Rudisha distance ikiwa ipo, kwa km."""
        if hasattr(obj, "distance") and obj.distance is not None:
            return round(obj.distance.km, 2)  # km kwa decimal mbili
        return None

    def to_representation(self, instance):
        """Ongeza labels za display."""
        rep = super().to_representation(instance)
        rep["billing_type_display"] = instance.get_billing_type_display()
        rep["location_type_display"] = instance.get_location_type_display()
        return rep


class TrendingServiceSerializer(serializers.ModelSerializer):
    business_id = serializers.UUIDField(source='business.id', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    billing_type_display = serializers.CharField(source="get_billing_type_display", read_only=True)
    order_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Service
        fields = [
            "id", "name", "description", "price", "billing_type", "billing_type_display",
            "business_id", "business_name", "order_count",
        ]


class ServiceListSerializer(serializers.ModelSerializer):
    """Serializer nyepesi kwa ajili ya orodha ya huduma (list view)."""
    distance = serializers.SerializerMethodField(
        help_text="Umbali kutoka kwa mtumiaji hadi huduma hii (ikiwa unapatikana)."
    )
    business_name = serializers.CharField(source="business.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    billing_type_display = serializers.CharField(source="get_billing_type_display", read_only=True)
    location_type_display = serializers.CharField(source="get_location_type_display", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "price",
            "is_available",
            "distance",
            "business_name",
            "category_name",
            "billing_type",
            "billing_type_display",
            "location_type",
            "location_type_display",
        ]
        read_only_fields = fields

    def get_distance(self, obj):
        if hasattr(obj, "distance") and obj.distance is not None:
            return round(obj.distance.km, 2)
        return None
