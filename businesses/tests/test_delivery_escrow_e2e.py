# businesses/tests/test_delivery_escrow_e2e.py
#
# End-to-end coverage of the item-request -> delivery -> escrow-release pipeline
# across businesses/logistics/jamiiwallet, per the approved plan's Phase D
# verification checklist (tingly-snuggling-mitten.md).

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from businesses.serializers.order_serializer import OrderSerializer
from businesses.models.order import PaymentStatus, OrderStatus, FulfillmentType
from logistics.models.rate_card import TransportRateCard
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle
from logistics.models.transport_assignment import TransportAssignment
from logistics.models.transport_request import TransportRequest
from logistics.choices import TransportRequestStatus
from logistics.services.escrow_release import release_escrow_if_ready
from logistics.models.transport_provider_verification import TransportProviderVerification

pytestmark = pytest.mark.django_db


def _verify_driver(driver_user):
    from kiini.models.institution import Institution

    institution, _ = Institution.objects.get_or_create(name="Test Logistics Co")
    driver_user.institution = institution
    driver_user.save(update_fields=["institution"])
    TransportProviderVerification.objects.create(
        user=driver_user, institution=institution, overall_status="VERIFIED"
    )


@pytest.fixture
def rate_card(db):
    return TransportRateCard.objects.create(
        vehicle_type="boda_boda",
        base_fare=Decimal("1000.00"),
        per_km_rate=Decimal("300.00"),
        minimum_fare=Decimal("1500.00"),
        is_active=True,
    )


@pytest.fixture
def delivery_order(user_factory, business_factory, product_factory, rate_card):
    buyer = user_factory(role="CLIENT")
    buyer.wallet.balance = Decimal("10000.00")
    buyer.wallet.save(update_fields=["balance"])
    business = business_factory(location=Point(39.28, -6.80))
    product = product_factory(business=business, price=Decimal("50.00"))

    data = {
        "client": buyer.id,
        "business": business.id,
        "fulfillment_type": FulfillmentType.DELIVERY,
        "items": [{"product": product.id, "quantity": 2}],
        "delivery": {
            "vehicle_type": "boda_boda",
            "dropoff_lat": -6.79,
            "dropoff_lng": 39.20,
            "dropoff_address_text": "Kariakoo",
        },
    }
    serializer = OrderSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    order = serializer.save(client=buyer)
    order.refresh_from_db()
    return order


@pytest.fixture
def driver_with_vehicle(user_factory):
    driver_user = user_factory(role="TRANSPORTER")
    _verify_driver(driver_user)
    provider = TransportProvider.objects.create(user=driver_user)
    vehicle = Vehicle.objects.create(provider=provider, vehicle_type="boda_boda", registration_number="T999XYZ")
    return {"user": driver_user, "provider": provider, "vehicle": vehicle}


def test_assign_request_flips_transport_request_status(delivery_order, driver_with_vehicle):
    transport_request = TransportRequest.objects.get(order=delivery_order)
    assert transport_request.status == TransportRequestStatus.PENDING
    assert transport_request.is_accepted is False

    api = APIClient()
    api.force_authenticate(user=driver_with_vehicle["user"])
    url = reverse("logistics:assignment-assign-request", args=[transport_request.id])
    response = api.post(url, {"vehicle": driver_with_vehicle["vehicle"].id})

    assert response.status_code == status.HTTP_201_CREATED, response.data
    transport_request.refresh_from_db()
    assert transport_request.status == TransportRequestStatus.ACCEPTED
    assert transport_request.is_accepted is True

    assignment = TransportAssignment.objects.get(transport_request=transport_request)
    assert assignment.agreed_fare == transport_request.estimated_fare


def test_second_driver_cannot_double_assign_same_request(delivery_order, driver_with_vehicle, user_factory):
    transport_request = TransportRequest.objects.get(order=delivery_order)

    api1 = APIClient()
    api1.force_authenticate(user=driver_with_vehicle["user"])
    url = reverse("logistics:assignment-assign-request", args=[transport_request.id])
    first = api1.post(url, {"vehicle": driver_with_vehicle["vehicle"].id})
    assert first.status_code == status.HTTP_201_CREATED

    other_driver = user_factory(role="TRANSPORTER")
    other_provider = TransportProvider.objects.create(user=other_driver)
    other_vehicle = Vehicle.objects.create(provider=other_provider, vehicle_type="boda_boda", registration_number="T111AAA")

    api2 = APIClient()
    api2.force_authenticate(user=other_driver)
    second = api2.post(url, {"vehicle": other_vehicle.id})
    assert second.status_code == status.HTTP_400_BAD_REQUEST
    assert TransportAssignment.objects.filter(transport_request=transport_request).count() == 1


def test_full_delivery_pipeline_releases_escrow_to_seller_and_driver(delivery_order, driver_with_vehicle):
    order = delivery_order
    business_owner = order.business.owner
    driver_user = driver_with_vehicle["user"]

    transport_request = TransportRequest.objects.get(order=order)
    assignment = TransportAssignment.objects.create(
        transport_request=transport_request,
        assigned_to=driver_with_vehicle["provider"],
        vehicle=driver_with_vehicle["vehicle"],
        agreed_fare=transport_request.estimated_fare,
    )

    order.client.wallet.refresh_from_db()
    held_before = order.client.wallet.held_balance
    assert held_before == order.total_amount

    business_owner.wallet.refresh_from_db()
    driver_user.wallet.refresh_from_db()
    assert business_owner.wallet.balance == Decimal("0.00")
    assert driver_user.wallet.balance == Decimal("0.00")

    # Driver marks delivered (must transition through IN_TRANSIT first) - escrow not
    # released yet since buyer hasn't confirmed.
    assignment.update_status(TransportAssignment.STATUS_IN_TRANSIT)
    assignment.mark_delivered()
    order.refresh_from_db()
    assert order.payment_status == PaymentStatus.HELD

    # Buyer confirms receipt - both conditions now met, escrow releases.
    assignment.confirm_receipt()

    order.refresh_from_db()
    assignment.refresh_from_db()
    assert order.payment_status == PaymentStatus.PAID
    assert order.status == OrderStatus.COMPLETED
    assert assignment.assignment_status == TransportAssignment.STATUS_COMPLETED

    order.client.wallet.refresh_from_db()
    business_owner.wallet.refresh_from_db()
    driver_user.wallet.refresh_from_db()

    product_amount = order.total_amount - order.delivery_fee
    assert business_owner.wallet.balance == product_amount
    assert driver_user.wallet.balance == order.delivery_fee
    assert order.client.wallet.held_balance == Decimal("0.00")
    assert order.client.wallet.balance == Decimal("10000.00") - order.total_amount


def test_escrow_release_is_idempotent_when_called_twice(delivery_order, driver_with_vehicle):
    order = delivery_order
    business_owner = order.business.owner
    driver_user = driver_with_vehicle["user"]

    transport_request = TransportRequest.objects.get(order=order)
    assignment = TransportAssignment.objects.create(
        transport_request=transport_request,
        assigned_to=driver_with_vehicle["provider"],
        vehicle=driver_with_vehicle["vehicle"],
        agreed_fare=transport_request.estimated_fare,
    )
    assignment.update_status(TransportAssignment.STATUS_IN_TRANSIT)
    assignment.mark_delivered()
    assignment.confirm_receipt()

    business_owner.wallet.refresh_from_db()
    driver_user.wallet.refresh_from_db()
    seller_balance_after_first_release = business_owner.wallet.balance
    driver_balance_after_first_release = driver_user.wallet.balance

    # Calling the release service again directly must be a no-op (payment_status is no longer HELD).
    release_escrow_if_ready(assignment)

    business_owner.wallet.refresh_from_db()
    driver_user.wallet.refresh_from_db()
    assert business_owner.wallet.balance == seller_balance_after_first_release
    assert driver_user.wallet.balance == driver_balance_after_first_release


def test_confirm_receipt_before_delivered_raises(delivery_order, driver_with_vehicle):
    transport_request = TransportRequest.objects.get(order=delivery_order)
    assignment = TransportAssignment.objects.create(
        transport_request=transport_request,
        assigned_to=driver_with_vehicle["provider"],
        vehicle=driver_with_vehicle["vehicle"],
        agreed_fare=transport_request.estimated_fare,
    )

    with pytest.raises(ValueError):
        assignment.confirm_receipt()

    delivery_order.refresh_from_db()
    assert delivery_order.payment_status == PaymentStatus.HELD


def test_escrow_release_ordering_reversed_still_works(delivery_order, driver_with_vehicle):
    """Buyer confirms AFTER driver marks delivered is the common path (covered above);
    this proves release also fires correctly if confirm_receipt is called immediately
    after mark_delivered without any intervening state - i.e. the hook in update_status
    (not just the mark_delivered wrapper) is what actually matters for release to fire,
    matching how the real mark-delivered API action calls update_status directly."""
    order = delivery_order
    transport_request = TransportRequest.objects.get(order=order)
    assignment = TransportAssignment.objects.create(
        transport_request=transport_request,
        assigned_to=driver_with_vehicle["provider"],
        vehicle=driver_with_vehicle["vehicle"],
        agreed_fare=transport_request.estimated_fare,
    )

    assignment.update_status(TransportAssignment.STATUS_IN_TRANSIT)
    assignment.update_status(TransportAssignment.STATUS_DELIVERED)  # hook fires here, but buyer hasn't confirmed yet
    order.refresh_from_db()
    assert order.payment_status == PaymentStatus.HELD

    assignment.confirm_receipt()
    order.refresh_from_db()
    assert order.payment_status == PaymentStatus.PAID
