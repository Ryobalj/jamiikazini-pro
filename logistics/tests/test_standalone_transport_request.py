# logistics/tests/test_standalone_transport_request.py
#
# Standalone transport requests: a plain buyer (no business/institution) asks
# for pure transport - "I need a boda-boda from A to B" - with no product
# order behind it. The fare is held from the requester's wallet at creation
# time (mirroring how a product order holds its delivery fee at checkout).

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from kiini.models.institution import Institution
from logistics.models.rate_card import TransportRateCard
from logistics.models.transport_provider import TransportProvider
from logistics.models.transport_provider_verification import TransportProviderVerification
from logistics.models.vehicle import Vehicle
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_assignment import TransportAssignment
from logistics.models.fare_proposal import FareProposal

pytestmark = pytest.mark.django_db

CREATE_URL = "/api/v1/logistics/transport-requests/"


@pytest.fixture
def rate_card(db):
    return TransportRateCard.objects.create(
        vehicle_type="boda_boda", base_fare=Decimal("1000.00"), per_km_rate=Decimal("300.00"),
        minimum_fare=Decimal("1500.00"), is_active=True,
    )


@pytest.fixture
def buyer(user_factory):
    u = user_factory(role="CLIENT")
    u.is_identity_verified = True
    u.is_phone_verified = True
    u.save(update_fields=["is_identity_verified", "is_phone_verified"])
    u.wallet.balance = Decimal("10000.00")
    u.wallet.save(update_fields=["balance"])
    return u


@pytest.fixture
def verified_driver(user_factory):
    institution, _ = Institution.objects.get_or_create(name="Standalone Test Logistics Co")
    driver_user = user_factory(role="TRANSPORTER")
    driver_user.institution = institution
    driver_user.save(update_fields=["institution"])
    provider = TransportProvider.objects.create(user=driver_user)
    vehicle = Vehicle.objects.create(provider=provider, vehicle_type="boda_boda", registration_number="T333STA")
    TransportProviderVerification.objects.create(user=driver_user, institution=institution, overall_status="VERIFIED")
    return {"user": driver_user, "provider": provider, "vehicle": vehicle}


def _payload(pickup=(39.28, -6.80), dropoff=(39.20, -6.79)):
    return {
        "package_description": "Boxes of clothes",
        "weight_kg": 5,
        "suggested_transport_type": "boda_boda",
        "pickup_location": {"type": "Point", "coordinates": list(pickup)},
        "dropoff_location": {"type": "Point", "coordinates": list(dropoff)},
        "pickup_address_text": "Dar es Salaam",
        "dropoff_address_text": "Kariakoo",
    }


class TestStandaloneRequestCreation:
    def test_individual_can_create_and_fare_is_held(self, buyer, rate_card):
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(CREATE_URL, _payload(), format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        tr = TransportRequest.objects.get(pk=response.data["id"])
        assert tr.requestor_type == "individual"
        assert tr.requested_by_id == buyer.id
        assert tr.estimated_fare is not None and tr.estimated_fare > 0

        buyer.wallet.refresh_from_db()
        assert buyer.wallet.held_balance == tr.estimated_fare
        assert buyer.wallet.balance == Decimal("10000.00")  # not deducted yet, only held

    def test_unverified_buyer_rejected(self, buyer, rate_card):
        buyer.is_identity_verified = False
        buyer.save(update_fields=["is_identity_verified"])
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(CREATE_URL, _payload(), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert TransportRequest.objects.count() == 0

    def test_insufficient_balance_rejected(self, buyer, rate_card):
        buyer.wallet.balance = Decimal("10.00")
        buyer.wallet.save(update_fields=["balance"])
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(CREATE_URL, _payload(), format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert TransportRequest.objects.count() == 0

    def test_missing_vehicle_type_rejected(self, buyer, rate_card):
        payload = _payload()
        del payload["suggested_transport_type"]
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(CREATE_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert TransportRequest.objects.count() == 0

    def test_unsuitable_vehicle_for_weight_rejected(self, buyer, rate_card):
        payload = _payload()
        payload["weight_kg"] = 5000  # far above boda_boda's ~100kg band
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(CREATE_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert TransportRequest.objects.count() == 0


class TestStandaloneRequestVisibility:
    def test_requester_can_retrieve_own_request(self, buyer, rate_card):
        api = APIClient()
        api.force_authenticate(user=buyer)
        created = api.post(CREATE_URL, _payload(), format="json").data

        response = api.get(f"{CREATE_URL}{created['id']}/")
        assert response.status_code == status.HTTP_200_OK

    def test_unrelated_user_cannot_retrieve_it(self, buyer, rate_card, user_factory):
        api = APIClient()
        api.force_authenticate(user=buyer)
        created = api.post(CREATE_URL, _payload(), format="json").data

        other = user_factory(role="CLIENT")
        api2 = APIClient()
        api2.force_authenticate(user=other)
        response = api2.get(f"{CREATE_URL}{created['id']}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStandaloneFastAcceptAndEscrow:
    def test_fast_accept_needs_no_extra_hold_since_fare_already_held(self, buyer, rate_card, verified_driver):
        api = APIClient()
        api.force_authenticate(user=buyer)
        created = api.post(CREATE_URL, _payload(), format="json").data
        buyer.wallet.refresh_from_db()
        held_after_create = buyer.wallet.held_balance

        driver_api = APIClient()
        driver_api.force_authenticate(user=verified_driver["user"])
        url = reverse("logistics:assignment-assign-request", args=[created["id"]])
        response = driver_api.post(url, {"vehicle": verified_driver["vehicle"].id})
        assert response.status_code == status.HTTP_201_CREATED, response.data

        buyer.wallet.refresh_from_db()
        assert buyer.wallet.held_balance == held_after_create  # unchanged - already held at creation

    def test_full_cycle_delivers_and_captures_fare_to_driver(self, buyer, rate_card, verified_driver):
        api = APIClient()
        api.force_authenticate(user=buyer)
        created = api.post(CREATE_URL, _payload(), format="json").data
        tr = TransportRequest.objects.get(pk=created["id"])
        fare = tr.estimated_fare

        driver_api = APIClient()
        driver_api.force_authenticate(user=verified_driver["user"])
        assign_url = reverse("logistics:assignment-assign-request", args=[created["id"]])
        assignment_id = driver_api.post(assign_url, {"vehicle": verified_driver["vehicle"].id}).data["id"]

        driver_api.post(reverse("logistics:assignment-mark-in-transit", args=[assignment_id]))
        driver_api.post(reverse("logistics:assignment-mark-delivered", args=[assignment_id]))

        api.post(reverse("logistics:assignment-confirm-receipt", args=[assignment_id]))

        buyer.wallet.refresh_from_db()
        verified_driver["user"].wallet.refresh_from_db()
        assignment = TransportAssignment.objects.get(pk=assignment_id)

        assert assignment.assignment_status == TransportAssignment.STATUS_COMPLETED
        assert buyer.wallet.held_balance == Decimal("0.00")
        assert buyer.wallet.balance == Decimal("10000.00") - fare
        assert verified_driver["user"].wallet.balance == fare

    def test_driver_cannot_confirm_receipt_of_others_request(self, buyer, rate_card, verified_driver):
        api = APIClient()
        api.force_authenticate(user=buyer)
        created = api.post(CREATE_URL, _payload(), format="json").data

        driver_api = APIClient()
        driver_api.force_authenticate(user=verified_driver["user"])
        assign_url = reverse("logistics:assignment-assign-request", args=[created["id"]])
        assignment_id = driver_api.post(assign_url, {"vehicle": verified_driver["vehicle"].id}).data["id"]
        driver_api.post(reverse("logistics:assignment-mark-in-transit", args=[assignment_id]))
        driver_api.post(reverse("logistics:assignment-mark-delivered", args=[assignment_id]))

        response = driver_api.post(reverse("logistics:assignment-confirm-receipt", args=[assignment_id]))
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStandaloneFareProposalApproval:
    def test_approving_higher_counter_offer_holds_the_difference(self, buyer, rate_card, verified_driver):
        api = APIClient()
        api.force_authenticate(user=buyer)
        created = api.post(CREATE_URL, _payload(), format="json").data
        tr = TransportRequest.objects.get(pk=created["id"])
        estimated = tr.estimated_fare
        buyer.wallet.refresh_from_db()
        held_before = buyer.wallet.held_balance

        driver_api = APIClient()
        driver_api.force_authenticate(user=verified_driver["user"])
        proposed_fare = estimated + Decimal("500.00")
        proposal_res = driver_api.post(
            "/api/v1/logistics/fare-proposals/",
            {
                "transport_request": created["id"],
                "vehicle": verified_driver["vehicle"].id,
                "proposed_fare": str(proposed_fare),
            },
            format="json",
        )
        assert proposal_res.status_code == status.HTTP_201_CREATED, proposal_res.data
        proposal_id = proposal_res.data["id"]

        approve_res = api.post(f"/api/v1/logistics/fare-proposals/{proposal_id}/approve/")
        assert approve_res.status_code == status.HTTP_200_OK, approve_res.data

        buyer.wallet.refresh_from_db()
        assert buyer.wallet.held_balance == held_before + Decimal("500.00")

        tr.refresh_from_db()
        assert tr.estimated_fare == proposed_fare

        assignment = TransportAssignment.objects.get(transport_request=tr)
        assert assignment.agreed_fare == proposed_fare
