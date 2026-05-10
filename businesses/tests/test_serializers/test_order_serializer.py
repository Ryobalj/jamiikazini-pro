# businesses/tests/test_serializers/test_order_serializer.py

import pytest
from decimal import Decimal
from django.utils import timezone
from businesses.serializers.order_serializer import OrderSerializer, OrderItemSerializer
from businesses.models.order import Order, OrderItem

pytestmark = pytest.mark.django_db


def test_order_serializer_create_valid(user_factory, business_factory, product_factory):
    client = user_factory(role="CLIENT")
    business = business_factory()
    product = product_factory(business=business, price=Decimal("10.00"))

    data = {
        "client": client.id,
        "business": business.id,
        "status": "PENDING",
        "payment_status": "UNPAID",
        "scheduled_datetime": timezone.now(),
        "notes": "Test order",
        "items": [
            {
                "product": product.id,
                "quantity": 2,
                "unit_price": "10.00"
            }
        ]
    }

    serializer = OrderSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    order = serializer.save()

    assert order.items.count() == 1
    assert order.total_amount == Decimal("20.00")


def test_order_serializer_invalid_missing_item(user_factory, business_factory):
    client = user_factory(role="CLIENT")
    business = business_factory()

    data = {
        "client": client.id,
        "business": business.id,
        "status": "PENDING",
        "payment_status": "UNPAID",
        "scheduled_datetime": timezone.now(),
        "notes": "Order bila items",
        "items": []
    }

    serializer = OrderSerializer(data=data)
    assert not serializer.is_valid()
    assert "Order lazima iwe na angalau item moja." in str(serializer.errors)


def test_order_item_serializer_validation(product_factory, business_factory):
    business = business_factory()
    product = product_factory(business=business, price=Decimal("15.00"))

    # Missing product or service (invalid)
    data_invalid = {
        "quantity": 1,
        "unit_price": "15.00"
    }
    serializer = OrderItemSerializer(data=data_invalid)
    assert not serializer.is_valid()
    assert "Lazima uchague Product au Service." in str(serializer.errors)

    # Valid with product
    data_valid = {
        "product": product.id,
        "quantity": 2,
        "unit_price": "10.00"
    }
    serializer = OrderItemSerializer(data=data_valid)
    assert serializer.is_valid()


def test_order_serializer_update(user_factory, business_factory, product_factory):
    client = user_factory(role="CLIENT")
    business = business_factory()
    product = product_factory(business=business, price=Decimal("5.00"))

    # Unda awali
    order = Order.objects.create(
        client=client,
        business=business,
        status="PENDING",
        payment_status="UNPAID",
        scheduled_datetime=timezone.now(),
        notes="Original"
    )
    OrderItem.objects.create(order=order, product=product, quantity=1, unit_price=Decimal("5.00"))

    # Fanya update
    update_data = {
        "client": client.id,
        "business": business.id,
        "status": "PROCESSING",
        "payment_status": "PAID",
        "scheduled_datetime": timezone.now(),
        "notes": "Updated",
        "items": [
            {
                "product": product.id,
                "quantity": 3,
                "unit_price": "10.00"
            }
        ]
    }

    serializer = OrderSerializer(instance=order, data=update_data)
    assert serializer.is_valid(), serializer.errors
    order = serializer.save()

    assert order.status == "PROCESSING"
    assert order.total_amount == Decimal("30.00")
    assert order.items.count() == 1
    assert order.items.first().quantity == 3