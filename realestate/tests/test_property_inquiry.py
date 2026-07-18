# realestate/tests/test_property_inquiry.py

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.test import APIClient

from payments.models.currency import Currency
from realestate.models.property_listing import PropertyListing, PropertyStatus
from realestate.models.property_inquiry import PropertyInquiry, PropertyInquiryStatus
from jamiiwallet.models.escrow_hold import EscrowHoldStatus

pytestmark = pytest.mark.django_db

INQUIRIES_URL = "/api/v1/realestate/inquiries/"


@pytest.fixture
def tzs(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def deal_setup(business_factory, user_factory, tzs):
    landlord = user_factory(role="PROVIDER")
    business = business_factory(owner=landlord, is_verified=True)

    tenant = user_factory(role="CLIENT")
    tenant.is_identity_verified = True
    tenant.is_phone_verified = True
    tenant.save(update_fields=["is_identity_verified", "is_phone_verified"])
    tenant.wallet.balance = Decimal("2000000.00")
    tenant.wallet.save(update_fields=["balance"])

    listing = PropertyListing.objects.create(
        owner=business, listing_type="RENT", property_type="APARTMENT",
        location=Point(39.2806, -6.8206, srid=4326), price=Decimal("400000.00"),
        deposit_amount=Decimal("400000.00"), currency=tzs, status=PropertyStatus.AVAILABLE,
    )
    return {"landlord": landlord, "business": business, "tenant": tenant, "listing": listing}


class TestCreateInquiry:
    def test_requires_identity_verification(self, deal_setup, user_factory):
        unverified = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=unverified)
        response = api.post(INQUIRIES_URL, {"property": str(deal_setup["listing"].id), "message": "Nataka kuona"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_buyer_creates_inquiry(self, deal_setup):
        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        response = api.post(INQUIRIES_URL, {"property": str(deal_setup["listing"].id), "message": "Nataka kuona"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == PropertyInquiryStatus.PENDING


class TestReserve:
    def _create_inquiry(self, deal_setup):
        return PropertyInquiry.objects.create(property=deal_setup["listing"], buyer=deal_setup["tenant"])

    def test_reserve_holds_funds_and_removes_listing_from_public_availability(self, deal_setup):
        inquiry = self._create_inquiry(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        response = api.post(f"{INQUIRIES_URL}{inquiry.id}/reserve/")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == PropertyInquiryStatus.RESERVED

        deal_setup["listing"].refresh_from_db()
        deal_setup["tenant"].wallet.refresh_from_db()
        assert deal_setup["listing"].status == PropertyStatus.RESERVED
        assert deal_setup["tenant"].wallet.held_balance == Decimal("800000.00")  # price + deposit

        inquiry.refresh_from_db()
        assert inquiry.escrow_hold.total_held == Decimal("800000.00")
        assert inquiry.escrow_hold.status == EscrowHoldStatus.OPEN

    def test_reserve_rejects_other_pending_inquiries_for_same_listing(self, deal_setup, user_factory):
        winner = self._create_inquiry(deal_setup)
        other_buyer = user_factory(role="CLIENT")
        other_buyer.is_identity_verified = True
        other_buyer.is_phone_verified = True
        other_buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])
        loser = PropertyInquiry.objects.create(property=deal_setup["listing"], buyer=other_buyer)

        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        api.post(f"{INQUIRIES_URL}{winner.id}/reserve/")

        loser.refresh_from_db()
        assert loser.status == PropertyInquiryStatus.REJECTED

    def test_reserve_fails_with_insufficient_balance(self, deal_setup):
        deal_setup["tenant"].wallet.balance = Decimal("100.00")
        deal_setup["tenant"].wallet.save(update_fields=["balance"])
        inquiry = self._create_inquiry(deal_setup)

        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        response = api.post(f"{INQUIRIES_URL}{inquiry.id}/reserve/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        deal_setup["listing"].refresh_from_db()
        assert deal_setup["listing"].status == PropertyStatus.AVAILABLE

    def test_cannot_reserve_already_reserved_listing(self, deal_setup, user_factory):
        first = self._create_inquiry(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        assert api.post(f"{INQUIRIES_URL}{first.id}/reserve/").status_code == status.HTTP_200_OK

        other_buyer = user_factory(role="CLIENT")
        other_buyer.is_identity_verified = True
        other_buyer.is_phone_verified = True
        other_buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])
        other_buyer.wallet.balance = Decimal("2000000.00")
        other_buyer.wallet.save(update_fields=["balance"])
        second = PropertyInquiry.objects.create(property=deal_setup["listing"], buyer=other_buyer)

        api.force_authenticate(user=other_buyer)
        response = api.post(f"{INQUIRIES_URL}{second.id}/reserve/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestConfirmHandover:
    def _reserved_inquiry(self, deal_setup):
        inquiry = PropertyInquiry.objects.create(property=deal_setup["listing"], buyer=deal_setup["tenant"])
        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        api.post(f"{INQUIRIES_URL}{inquiry.id}/reserve/")
        inquiry.refresh_from_db()
        return inquiry

    def test_single_side_confirmation_does_not_release_funds(self, deal_setup):
        inquiry = self._reserved_inquiry(deal_setup)
        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        response = api.post(f"{INQUIRIES_URL}{inquiry.id}/confirm-handover/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == PropertyInquiryStatus.RESERVED
        deal_setup["landlord"].wallet.refresh_from_db()
        assert deal_setup["landlord"].wallet.balance == Decimal("0.00")

    def test_both_sides_confirming_releases_funds_and_completes(self, deal_setup):
        inquiry = self._reserved_inquiry(deal_setup)
        api = APIClient()

        api.force_authenticate(user=deal_setup["tenant"])
        api.post(f"{INQUIRIES_URL}{inquiry.id}/confirm-handover/")

        api.force_authenticate(user=deal_setup["landlord"])
        response = api.post(f"{INQUIRIES_URL}{inquiry.id}/confirm-handover/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == PropertyInquiryStatus.COMPLETED

        deal_setup["listing"].refresh_from_db()
        deal_setup["landlord"].wallet.refresh_from_db()
        deal_setup["tenant"].wallet.refresh_from_db()
        assert deal_setup["listing"].status == PropertyStatus.RENTED
        assert deal_setup["landlord"].wallet.balance == Decimal("800000.00")
        assert deal_setup["tenant"].wallet.held_balance == Decimal("0.00")

    def test_stranger_cannot_confirm_handover(self, deal_setup, user_factory):
        inquiry = self._reserved_inquiry(deal_setup)
        stranger = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=stranger)
        response = api.post(f"{INQUIRIES_URL}{inquiry.id}/confirm-handover/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCancel:
    def test_buyer_cancels_reserved_inquiry_and_funds_return(self, deal_setup):
        inquiry = PropertyInquiry.objects.create(property=deal_setup["listing"], buyer=deal_setup["tenant"])
        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        api.post(f"{INQUIRIES_URL}{inquiry.id}/reserve/")

        response = api.post(f"{INQUIRIES_URL}{inquiry.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == PropertyInquiryStatus.CANCELLED

        deal_setup["listing"].refresh_from_db()
        deal_setup["tenant"].wallet.refresh_from_db()
        assert deal_setup["listing"].status == PropertyStatus.AVAILABLE
        assert deal_setup["tenant"].wallet.held_balance == Decimal("0.00")
        assert deal_setup["tenant"].wallet.balance == Decimal("2000000.00")

    def test_owner_can_also_cancel(self, deal_setup):
        inquiry = PropertyInquiry.objects.create(property=deal_setup["listing"], buyer=deal_setup["tenant"])
        api = APIClient()
        api.force_authenticate(user=deal_setup["tenant"])
        api.post(f"{INQUIRIES_URL}{inquiry.id}/reserve/")

        api.force_authenticate(user=deal_setup["landlord"])
        response = api.post(f"{INQUIRIES_URL}{inquiry.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK
