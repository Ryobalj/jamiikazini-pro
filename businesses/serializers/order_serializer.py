from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from businesses.models.order import Order,OrderItem
from businesses.models.product import Product
from businesses.models.service import Service


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "service", "quantity", "unit_price", "total_price", "order"]
        read_only_fields = ["id", "total_price", "order"]

    def validate(self, attrs):
        if not attrs.get("product") and not attrs.get("service"):
            raise serializers.ValidationError("Lazima uchague Product au Service.")
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "client",
            "business",
            "status",
            "payment_status",
            "scheduled_datetime",
            "notes",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "client", "total_amount", "created_at", "updated_at"]  # client = request.user (view)

    def validate(self, attrs):
        # Items ni lazima wakati wa CREATE tu; partial update (mf. notes) isidai items
        if self.instance is None:
            items = self.initial_data.get("items", [])
            if not items:
                raise serializers.ValidationError("Order lazima iwe na angalau item moja.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        # Recalculate total
        order.total_amount = order.calculate_total()
        order.save(update_fields=["total_amount"])
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        # items ni hiari kwenye partial update - usifute items zilizopo bila mpya
        items_data = validated_data.pop("items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is None:
            return instance

        # Delete old items and recreate
        instance.items.all().delete()
        for item_data in items_data:
            OrderItem.objects.create(order=instance, **item_data)

        instance.total_amount = instance.calculate_total()
        instance.save(update_fields=["total_amount"])
        return instance
