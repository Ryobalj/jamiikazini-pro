# businesses/serializers/item_request_serializer.py

from decimal import Decimal
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers

from businesses.models.item_request import ItemRequest, ItemRequestStatus
from businesses.models.product_category import ProductCategory

REQUEST_EXPIRY_MINUTES = 30


class ItemRequestSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True, default=None)
    claimed_by_business_name = serializers.CharField(source="claimed_by_business.name", read_only=True, default=None)
    claimed_product_name = serializers.CharField(source="claimed_product.name", read_only=True, default=None)
    matched_products_count = serializers.SerializerMethodField()

    class Meta:
        model = ItemRequest
        fields = [
            "id", "buyer", "buyer_name", "product_name_query", "category", "quantity",
            "address_text", "radius_km", "status",
            "claimed_by_business", "claimed_by_business_name",
            "claimed_product", "claimed_product_name", "claimed_at",
            "order", "expires_at", "matched_products_count", "created_at",
        ]
        read_only_fields = fields

    def get_matched_products_count(self, obj):
        return len(obj.matched_product_ids or [])


class ItemRequestCreateSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=255)
    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), required=False, allow_null=True
    )
    quantity = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0.001"), default=Decimal("1")
    )
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    radius_km = serializers.IntegerField(min_value=1, max_value=50, default=5)

    def create(self, validated_data):
        from django.contrib.gis.db.models.functions import Distance
        from businesses.models.product import Product

        request = self.context["request"]
        q = validated_data["q"].strip()
        category = validated_data.get("category")
        quantity = validated_data["quantity"]
        radius_km = validated_data["radius_km"]
        location = Point(validated_data["lng"], validated_data["lat"], srid=4326)

        candidates = Product.objects.filter(
            is_available=True,
            quantity_in_stock__gte=quantity,
            name__icontains=q,
            business__is_active=True,
        ).annotate(
            distance=Distance("business__location", location)
        ).filter(distance__lte=radius_km * 1000)

        if category:
            candidates = candidates.filter(category=category)

        matched_ids = list(candidates.values_list("id", flat=True))
        if not matched_ids:
            raise serializers.ValidationError(
                {"q": "Hakuna bidhaa inayolingana karibu nawe. Jaribu kupanua eneo la utafutaji."}
            )

        item_request = ItemRequest.objects.create(
            buyer=request.user,
            product_name_query=q,
            category=category,
            matched_product_ids=matched_ids,
            quantity=quantity,
            location=location,
            radius_km=radius_km,
            status=ItemRequestStatus.PENDING,
            expires_at=timezone.now() + timedelta(minutes=REQUEST_EXPIRY_MINUTES),
        )

        self._notify_matched_businesses(candidates)
        return item_request

    @staticmethod
    def _notify_matched_businesses(candidates):
        from kiini.helpers.notification_helper import notify_user

        notified_owners = set()
        for product in candidates.select_related("business__owner"):
            owner = product.business.owner
            if owner.id in notified_owners:
                continue
            notified_owners.add(owner.id)
            notify_user(owner, "Kuna ombi jipya la bidhaa karibu na biashara yako kwenye Jamiikazini.")


class ItemRequestClaimSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
