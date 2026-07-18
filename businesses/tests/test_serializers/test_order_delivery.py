# businesses/tests/test_serializers/test_order_delivery.py

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from rest_framework import serializers
from businesses.serializers.order_serializer import OrderSerializer
from businesses.models.order import Order, PaymentStatus, FulfillmentType
from logistics.models.rate_card import TransportRateCard
from logistics.models.transport_request import TransportRequest

pytestmark = pytest.mark.django_db


@pytest.fixture
def rate_card(db):
    return TransportRateCard.objects.create(
        vehicle_type="boda_boda",
        base_fare=Decimal("1000.00"),
        per_km_rate=Decimal("300.00"),
        minimum_fare=Decimal("1500.00"),
        is_active=True,
    )


def _delivery_data(vehicle_type="boda_boda", dropoff_lat=-6.79, dropoff_lng=39.20):
    return {
        "vehicle_type": vehicle_type,
        "dropoff_lat": dropoff_lat,
        "dropoff_lng": dropoff_lng,
        "dropoff_address_text": "Kariakoo",
    }


def test_delivery_order_holds_funds_and_creates_transport_request(
    user_factory, business_factory, product_factory, rate_card
):
    client = user_factory(role="CLIENT")
    client.wallet.balance = Decimal("10000.00")
    client.wallet.save(update_fields=["balance"])
    business = business_factory(location=Point(39.28, -6.80))
    product = product_factory(business=business, price=Decimal("50.00"))

    data = {
        "client": client.id,
        "business": business.id,
        "fulfillment_type": FulfillmentType.DELIVERY,
        "items": [{"product": product.id, "quantity": 2}],
        "delivery": _delivery_data(),
    }

    serializer = OrderSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    order = serializer.save(client=client)
    order.refresh_from_db()  # normalize to DB-rounded Decimal precision for comparisons below

    assert order.fulfillment_type == FulfillmentType.DELIVERY
    assert order.payment_status == PaymentStatus.HELD
    assert order.delivery_fee > Decimal("0.00")
    assert order.total_amount == order.items.first().total_price + order.delivery_fee

    client.wallet.refresh_from_db()
    # Balance untouched (nothing captured yet) - only held_balance carries the escrow.
    assert client.wallet.balance == Decimal("10000.00")
    assert client.wallet.held_balance == order.total_amount
    assert client.wallet.available_balance == Decimal("10000.00") - order.total_amount

    transport_request = TransportRequest.objects.get(order=order)
    assert transport_request.suggested_transport_type == "boda_boda"
    assert transport_request.estimated_fare == order.delivery_fee
    assert transport_request.business_id == business.id


def test_delivery_order_fails_cleanly_on_insufficient_balance(
    user_factory, business_factory, product_factory, rate_card
):
    client = user_factory(role="CLIENT")  # balance = 0 by default
    business = business_factory(location=Point(39.28, -6.80))
    product = product_factory(business=business, price=Decimal("50.00"))
    stock_before = product.quantity_in_stock

    data = {
        "client": client.id,
        "business": business.id,
        "fulfillment_type": FulfillmentType.DELIVERY,
        "items": [{"product": product.id, "quantity": 1}],
        "delivery": _delivery_data(),
    }

    serializer = OrderSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(serializers.ValidationError):
        serializer.save(client=client)

    assert not Order.objects.filter(client=client).exists()
    assert not TransportRequest.objects.filter(business=business).exists()
    product.refresh_from_db()
    assert product.quantity_in_stock == stock_before
    client.wallet.refresh_from_db()
    assert client.wallet.held_balance == Decimal("0.00")


def test_delivery_order_fails_when_business_has_no_location(
    user_factory, business_factory, product_factory, rate_card
):
    client = user_factory(role="CLIENT")
    client.wallet.balance = Decimal("500.00")
    client.wallet.save(update_fields=["balance"])
    business = business_factory()  # no location set
    product = product_factory(business=business, price=Decimal("50.00"))

    data = {
        "client": client.id,
        "business": business.id,
        "fulfillment_type": FulfillmentType.DELIVERY,
        "items": [{"product": product.id, "quantity": 1}],
        "delivery": _delivery_data(),
    }

    serializer = OrderSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(serializers.ValidationError):
        serializer.save(client=client)

    assert not Order.objects.filter(client=client).exists()


def test_delivery_order_rejected_when_vehicle_unsuitable_for_weight(
    user_factory, business_factory, product_factory, rate_card
):
    """A tiny 1kg local order requesting 'ship' must be rejected - ship's weight/
    distance band (>=2000kg, >=250km) doesn't fit a small nearby delivery."""
    TransportRateCard.objects.create(
        vehicle_type="ship", base_fare=Decimal("80000.00"), per_km_rate=Decimal("3000.00"),
        minimum_fare=Decimal("100000.00"), is_active=True,
    )
    client = user_factory(role="CLIENT")
    client.wallet.balance = Decimal("500000.00")
    client.wallet.save(update_fields=["balance"])
    business = business_factory(location=Point(39.28, -6.80))
    product = product_factory(business=business, price=Decimal("50.00"))

    data = {
        "client": client.id,
        "business": business.id,
        "fulfillment_type": FulfillmentType.DELIVERY,
        "items": [{"product": product.id, "quantity": 1}],
        "delivery": {**_delivery_data(vehicle_type="ship"), "weight_kg": 1},
    }

    serializer = OrderSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(serializers.ValidationError):
        serializer.save(client=client)

    assert not Order.objects.filter(client=client).exists()


def test_pickup_order_unaffected_by_delivery_branch(user_factory, business_factory, product_factory):
    """Sanity check: omitting fulfillment_type/delivery still takes the original, unchanged PICKUP path."""
    client = user_factory(role="CLIENT")
    client.wallet.balance = Decimal("100.00")
    client.wallet.save(update_fields=["balance"])
    business = business_factory()
    product = product_factory(business=business, price=Decimal("10.00"))

    data = {
        "client": client.id,
        "business": business.id,
        "items": [{"product": product.id, "quantity": 2}],
    }

    serializer = OrderSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    order = serializer.save(client=client)

    assert order.fulfillment_type == FulfillmentType.PICKUP
    assert order.payment_status == PaymentStatus.PAID
    assert order.delivery_fee == Decimal("0.00")
    client.wallet.refresh_from_db()
    assert client.wallet.balance == Decimal("80.00")
    assert client.wallet.held_balance == Decimal("0.00")
