# agriculture/tests/test_harvest_contract.py

import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from payments.models.currency import Currency
from agriculture.models.harvest_contract import HarvestContract, HarvestContractStatus
from jamiiwallet.models.escrow_hold import EscrowHoldStatus

pytestmark = pytest.mark.django_db

CONTRACTS_URL = "/api/v1/agriculture/contracts/"


@pytest.fixture
def tzs(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def deal_setup(business_factory, user_factory, tzs):
    farmer = user_factory(role="PROVIDER")
    business = business_factory(owner=farmer, is_verified=True, deals_in_agriculture=True)

    buyer = user_factory(role="CLIENT")
    buyer.is_identity_verified = True
    buyer.is_phone_verified = True
    buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])
    buyer.wallet.balance = Decimal("5000000.00")
    buyer.wallet.save(update_fields=["balance"])

    return {"farmer": farmer, "business": business, "buyer": buyer}


def _dates():
    start = date.today() + timedelta(days=30)
    end = start + timedelta(days=10)
    return start.isoformat(), end.isoformat()


class TestCreateContract:
    def test_requires_identity_verification(self, deal_setup, user_factory):
        unverified = user_factory(role="CLIENT")
        start, end = _dates()
        api = APIClient()
        api.force_authenticate(user=unverified)
        response = api.post(CONTRACTS_URL, {
            "crop_description": "Mahindi", "estimated_weight_kg": "1000.000",
            "agreed_price_per_kg": "800.00", "delivery_window_start": start, "delivery_window_end": end,
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_buyer_creates_contract(self, deal_setup):
        start, end = _dates()
        api = APIClient()
        api.force_authenticate(user=deal_setup["buyer"])
        response = api.post(CONTRACTS_URL, {
            "crop_description": "Mahindi", "estimated_weight_kg": "1000.000",
            "agreed_price_per_kg": "800.00", "delivery_window_start": start, "delivery_window_end": end,
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["status"] == HarvestContractStatus.PENDING
        assert Decimal(response.data["deposit_amount"]) == Decimal("240000.00")  # 30% of 800,000

    def test_invalid_delivery_window_rejected(self, deal_setup):
        start, end = _dates()
        api = APIClient()
        api.force_authenticate(user=deal_setup["buyer"])
        response = api.post(CONTRACTS_URL, {
            "crop_description": "Mahindi", "estimated_weight_kg": "1000.000",
            "agreed_price_per_kg": "800.00", "delivery_window_start": end, "delivery_window_end": start,
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestClaim:
    def _make_contract(self, deal_setup):
        start, end = _dates()
        return HarvestContract.objects.create(
            buyer=deal_setup["buyer"], crop_description="Mahindi",
            estimated_weight_kg=Decimal("1000.000"), agreed_price_per_kg=Decimal("800.00"),
            delivery_window_start=start, delivery_window_end=end,
        )

    def test_farmer_sees_pending_contract_via_incoming(self, deal_setup):
        contract = self._make_contract(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["farmer"])
        response = api.get(f"{CONTRACTS_URL}incoming/")
        assert response.status_code == status.HTTP_200_OK
        assert any(c["id"] == str(contract.id) for c in response.data)

    def test_claim_opens_deposit_hold(self, deal_setup):
        contract = self._make_contract(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["farmer"])
        response = api.post(f"{CONTRACTS_URL}{contract.id}/claim/", {
            "business_id": str(deal_setup["business"].id),
        }, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == HarvestContractStatus.ACCEPTED

        contract.refresh_from_db()
        deal_setup["buyer"].wallet.refresh_from_db()
        assert contract.escrow_hold.total_held == Decimal("240000.00")
        assert contract.escrow_hold.status == EscrowHoldStatus.OPEN
        assert deal_setup["buyer"].wallet.held_balance == Decimal("240000.00")

    def test_claim_rejected_for_non_agriculture_business(self, deal_setup, business_factory, user_factory):
        contract = self._make_contract(deal_setup)
        owner = user_factory(role="PROVIDER")
        business = business_factory(owner=owner, is_verified=True)  # deals_in_agriculture=False
        api = APIClient()
        api.force_authenticate(user=owner)
        response = api.post(f"{CONTRACTS_URL}{contract.id}/claim/", {"business_id": str(business.id)}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_claim_rejected_for_unverified_business(self, deal_setup, business_factory, user_factory):
        contract = self._make_contract(deal_setup)
        owner = user_factory(role="PROVIDER")
        business = business_factory(owner=owner, is_verified=False, deals_in_agriculture=True)
        api = APIClient()
        api.force_authenticate(user=owner)
        response = api.post(f"{CONTRACTS_URL}{contract.id}/claim/", {"business_id": str(business.id)}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_claim_twice(self, deal_setup):
        contract = self._make_contract(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["farmer"])
        first = api.post(f"{CONTRACTS_URL}{contract.id}/claim/", {"business_id": str(deal_setup["business"].id)}, format="json")
        assert first.status_code == status.HTTP_200_OK
        second = api.post(f"{CONTRACTS_URL}{contract.id}/claim/", {"business_id": str(deal_setup["business"].id)}, format="json")
        assert second.status_code == status.HTTP_400_BAD_REQUEST


class TestConfirmDelivery:
    def _accepted_contract(self, deal_setup):
        start, end = _dates()
        contract = HarvestContract.objects.create(
            buyer=deal_setup["buyer"], crop_description="Mahindi",
            estimated_weight_kg=Decimal("1000.000"), agreed_price_per_kg=Decimal("800.00"),
            delivery_window_start=start, delivery_window_end=end,
        )
        api = APIClient()
        api.force_authenticate(user=deal_setup["farmer"])
        api.post(f"{CONTRACTS_URL}{contract.id}/claim/", {"business_id": str(deal_setup["business"].id)}, format="json")
        contract.refresh_from_db()
        return contract

    def test_matching_weights_settle_and_pay_extra(self, deal_setup):
        contract = self._accepted_contract(deal_setup)
        api = APIClient()

        # Delivered weight (1050kg) exceeds estimate (1000kg) - final amount
        # exceeds the 30% deposit, so an extra PAYMENT must cover the rest.
        api.force_authenticate(user=deal_setup["buyer"])
        api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "1050.000"}, format="json")

        api.force_authenticate(user=deal_setup["farmer"])
        response = api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "1050.000"}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == HarvestContractStatus.SETTLED

        contract.refresh_from_db()
        deal_setup["buyer"].wallet.refresh_from_db()
        deal_setup["farmer"].wallet.refresh_from_db()

        final_amount = Decimal("1050.000") * Decimal("800.00")  # 840,000
        assert deal_setup["farmer"].wallet.balance == final_amount
        assert deal_setup["buyer"].wallet.held_balance == Decimal("0.00")
        # 5,000,000 - 240,000 (deposit, already left balance at claim) - 600,000 (extra payment)
        assert deal_setup["buyer"].wallet.balance == Decimal("5000000.00") - final_amount

    def test_matching_lower_weight_refunds_excess_deposit(self, deal_setup):
        contract = self._accepted_contract(deal_setup)
        api = APIClient()

        # Delivered weight (900kg) is below estimate - final amount is less
        # than the 30% deposit, so the excess must be voided back to buyer.
        api.force_authenticate(user=deal_setup["buyer"])
        api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "900.000"}, format="json")
        api.force_authenticate(user=deal_setup["farmer"])
        api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "900.000"}, format="json")

        contract.refresh_from_db()
        deal_setup["buyer"].wallet.refresh_from_db()
        deal_setup["farmer"].wallet.refresh_from_db()

        final_amount = Decimal("900.000") * Decimal("800.00")  # 720,000
        assert contract.status == HarvestContractStatus.SETTLED
        assert deal_setup["farmer"].wallet.balance == final_amount
        assert deal_setup["buyer"].wallet.held_balance == Decimal("0.00")
        assert deal_setup["buyer"].wallet.balance == Decimal("5000000.00") - final_amount

    def test_single_side_confirmation_does_not_settle(self, deal_setup):
        contract = self._accepted_contract(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["buyer"])
        response = api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "1000.000"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == HarvestContractStatus.ACCEPTED

    def test_mismatched_weights_beyond_tolerance_dispute(self, deal_setup):
        contract = self._accepted_contract(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["buyer"])
        api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "1000.000"}, format="json")
        api.force_authenticate(user=deal_setup["farmer"])
        response = api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "700.000"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == HarvestContractStatus.DISPUTED

        contract.refresh_from_db()
        deal_setup["buyer"].wallet.refresh_from_db()
        # Hold stays frozen - no capture, no void.
        assert deal_setup["buyer"].wallet.held_balance == Decimal("240000.00")
        assert contract.escrow_hold.status == EscrowHoldStatus.OPEN

    def test_stranger_cannot_confirm_delivery(self, deal_setup, user_factory):
        contract = self._accepted_contract(deal_setup)
        stranger = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=stranger)
        response = api.post(f"{CONTRACTS_URL}{contract.id}/confirm-delivery/", {"delivered_weight_kg": "1000.000"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCancel:
    def test_buyer_cancels_pending_contract(self, deal_setup):
        start, end = _dates()
        contract = HarvestContract.objects.create(
            buyer=deal_setup["buyer"], crop_description="Mahindi",
            estimated_weight_kg=Decimal("1000.000"), agreed_price_per_kg=Decimal("800.00"),
            delivery_window_start=start, delivery_window_end=end,
        )
        api = APIClient()
        api.force_authenticate(user=deal_setup["buyer"])
        response = api.post(f"{CONTRACTS_URL}{contract.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == HarvestContractStatus.CANCELLED

    def test_cancel_accepted_contract_refunds_deposit(self, deal_setup):
        start, end = _dates()
        contract = HarvestContract.objects.create(
            buyer=deal_setup["buyer"], crop_description="Mahindi",
            estimated_weight_kg=Decimal("1000.000"), agreed_price_per_kg=Decimal("800.00"),
            delivery_window_start=start, delivery_window_end=end,
        )
        api = APIClient()
        api.force_authenticate(user=deal_setup["farmer"])
        api.post(f"{CONTRACTS_URL}{contract.id}/claim/", {"business_id": str(deal_setup["business"].id)}, format="json")

        response = api.post(f"{CONTRACTS_URL}{contract.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK

        deal_setup["buyer"].wallet.refresh_from_db()
        assert deal_setup["buyer"].wallet.held_balance == Decimal("0.00")
        assert deal_setup["buyer"].wallet.balance == Decimal("5000000.00")
