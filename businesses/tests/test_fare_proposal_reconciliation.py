# businesses/tests/test_fare_proposal_reconciliation.py

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from businesses.serializers.order_serializer import OrderSerializer
from businesses.models.order import FulfillmentType
from logistics.models.rate_card import TransportRateCard
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle
from logistics.models.fare_proposal import FareProposal, FareProposalStatus
from logistics.models.transport_request import TransportRequest
from logistics.choices import TransportRequestStatus
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
    vehicle = Vehicle.objects.create(provider=provider, vehicle_type="boda_boda", registration_number="T555ZZZ")
    return {"user": driver_user, "provider": provider, "vehicle": vehicle}


def _propose(transport_request, driver, fare):
    api = APIClient()
    api.force_authenticate(user=driver["user"])
    return api.post(
        "/api/v1/logistics/fare-proposals/",
        {"transport_request": str(transport_request.id), "vehicle": driver["vehicle"].id, "proposed_fare": str(fare)},
        format="json",
    )


def _approve(proposal_id, buyer):
    api = APIClient()
    api.force_authenticate(user=buyer)
    return api.post(f"/api/v1/logistics/fare-proposals/{proposal_id}/approve/")


def test_higher_counter_offer_places_incremental_hold_on_approval(delivery_order, driver_with_vehicle):
    transport_request = TransportRequest.objects.get(order=delivery_order)
    estimated = transport_request.estimated_fare
    higher_fare = estimated + Decimal("500.00")

    propose_res = _propose(transport_request, driver_with_vehicle, higher_fare)
    assert propose_res.status_code == status.HTTP_201_CREATED, propose_res.data

    approve_res = _approve(propose_res.data["id"], delivery_order.client)
    assert approve_res.status_code == status.HTTP_200_OK, approve_res.data
    assert Decimal(approve_res.data["agreed_fare"]) == higher_fare

    delivery_order.refresh_from_db()
    assert delivery_order.delivery_fee == estimated + Decimal("500.00")

    delivery_order.client.wallet.refresh_from_db()
    assert delivery_order.client.wallet.held_balance == delivery_order.total_amount

    transport_request.refresh_from_db()
    assert transport_request.status == TransportRequestStatus.ACCEPTED

    proposal = FareProposal.objects.get(pk=propose_res.data["id"])
    assert proposal.status == FareProposalStatus.APPROVED


def test_lower_counter_offer_voids_the_difference_on_approval(delivery_order, driver_with_vehicle):
    transport_request = TransportRequest.objects.get(order=delivery_order)
    estimated = transport_request.estimated_fare
    lower_fare = estimated - Decimal("300.00")
    assert lower_fare > 0

    propose_res = _propose(transport_request, driver_with_vehicle, lower_fare)
    assert propose_res.status_code == status.HTTP_201_CREATED, propose_res.data

    original_total = delivery_order.total_amount
    approve_res = _approve(propose_res.data["id"], delivery_order.client)
    assert approve_res.status_code == status.HTTP_200_OK, approve_res.data

    delivery_order.refresh_from_db()
    assert delivery_order.delivery_fee == estimated - Decimal("300.00")
    assert delivery_order.total_amount == original_total - Decimal("300.00")

    delivery_order.client.wallet.refresh_from_db()
    # Held balance shrinks to match the now-lower total - the 300 excess was voided back.
    assert delivery_order.client.wallet.held_balance == delivery_order.total_amount


def test_approval_blocked_when_higher_offer_exceeds_available_balance(delivery_order, driver_with_vehicle):
    transport_request = TransportRequest.objects.get(order=delivery_order)
    # Drain the buyer's remaining available balance so the incremental hold can't fit.
    delivery_order.client.wallet.refresh_from_db()
    delivery_order.client.wallet.balance = delivery_order.client.wallet.held_balance
    delivery_order.client.wallet.save(update_fields=["balance"])

    huge_fare = transport_request.estimated_fare + Decimal("1000.00")
    propose_res = _propose(transport_request, driver_with_vehicle, huge_fare)
    assert propose_res.status_code == status.HTTP_201_CREATED, propose_res.data

    approve_res = _approve(propose_res.data["id"], delivery_order.client)
    assert approve_res.status_code == status.HTTP_400_BAD_REQUEST

    proposal = FareProposal.objects.get(pk=propose_res.data["id"])
    assert proposal.status == FareProposalStatus.PENDING  # unchanged - approval never committed

    transport_request.refresh_from_db()
    assert transport_request.status == TransportRequestStatus.PENDING

    delivery_order.refresh_from_db()
    assert delivery_order.total_amount == delivery_order.client.wallet.held_balance


def test_fast_accept_blocks_pending_proposal_approval(delivery_order, driver_with_vehicle, user_factory):
    transport_request = TransportRequest.objects.get(order=delivery_order)

    propose_res = _propose(transport_request, driver_with_vehicle, transport_request.estimated_fare + Decimal("200.00"))
    assert propose_res.status_code == status.HTTP_201_CREATED

    # A different driver fast-accepts the same job while the proposal is still pending.
    other_driver_user = user_factory(role="TRANSPORTER")
    _verify_driver(other_driver_user)
    other_provider = TransportProvider.objects.create(user=other_driver_user)
    other_vehicle = Vehicle.objects.create(provider=other_provider, vehicle_type="boda_boda", registration_number="T777QQQ")

    api = APIClient()
    api.force_authenticate(user=other_driver_user)
    url = reverse("logistics:assignment-assign-request", args=[transport_request.id])
    fast_accept_res = api.post(url, {"vehicle": other_vehicle.id})
    assert fast_accept_res.status_code == status.HTTP_201_CREATED

    approve_res = _approve(propose_res.data["id"], delivery_order.client)
    assert approve_res.status_code == status.HTTP_400_BAD_REQUEST
