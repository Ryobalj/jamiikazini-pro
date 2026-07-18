# billpay/tests/test_bill_payment.py

import pytest
from decimal import Decimal
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIClient

from gov_integration.models.country_config import CountryConfig
from billpay.models.biller import Biller, BillerCategory
from billpay.models.bill_payment import BillPayment, BillPaymentStatus
from jamiiwallet.models.transaction import Transaction

pytestmark = pytest.mark.django_db

BILLERS_URL = "/api/v1/billpay/billers/"
PAYMENTS_URL = "/api/v1/billpay/payments/"


@pytest.fixture
def tz(db):
    return CountryConfig.objects.get_or_create(code="TZ", defaults={"name": "Tanzania"})[0]


@pytest.fixture
def luku(tz):
    return Biller.objects.create(
        name="LUKU (TANESCO)", category=BillerCategory.ELECTRICITY, country=tz, config_key="TZ_LUKU",
    )


@pytest.fixture
def buyer(user_factory):
    user = user_factory(role="CLIENT")
    user.is_identity_verified = True
    user.is_phone_verified = True
    user.save(update_fields=["is_identity_verified", "is_phone_verified"])
    user.wallet.balance = Decimal("50000.00")
    user.wallet.save(update_fields=["balance"])
    return user


class TestListBillers:
    def test_anyone_can_list_active_billers(self, luku):
        api = APIClient()
        response = api.get(BILLERS_URL)
        assert response.status_code == status.HTTP_200_OK
        data = response.data if isinstance(response.data, list) else response.data["results"]
        assert any(b["id"] == str(luku.id) for b in data)

    def test_inactive_biller_excluded(self, tz):
        inactive = Biller.objects.create(
            name="Old Biller", category=BillerCategory.WATER, country=tz, config_key="TZ_WATER", is_active=False,
        )
        api = APIClient()
        response = api.get(BILLERS_URL)
        data = response.data if isinstance(response.data, list) else response.data["results"]
        assert not any(b["id"] == str(inactive.id) for b in data)


class TestCreateBillPayment:
    def test_requires_identity_verification(self, luku, user_factory):
        user = user_factory(role="CLIENT")
        user.wallet.balance = Decimal("5000.00")
        user.wallet.save(update_fields=["balance"])
        api = APIClient()
        api.force_authenticate(user=user)
        response = api.post(PAYMENTS_URL, {
            "biller": str(luku.id), "account_number": "12345678", "amount": "1000.00",
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_successful_payment_debits_wallet_and_completes(self, luku, buyer):
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(PAYMENTS_URL, {
            "biller": str(luku.id), "account_number": "12345678", "amount": "1000.00",
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["status"] == BillPaymentStatus.COMPLETED

        buyer.wallet.refresh_from_db()
        assert buyer.wallet.balance == Decimal("49000.00")

        bill_payment = BillPayment.objects.get(user=buyer)
        assert bill_payment.status == BillPaymentStatus.COMPLETED
        assert bill_payment.wallet_transaction.transaction_type == Transaction.TransactionType.WITHDRAWAL
        assert bill_payment.wallet_transaction.status == Transaction.TransactionStatus.COMPLETED

    def test_electricity_payment_returns_token(self, luku, buyer):
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(PAYMENTS_URL, {
            "biller": str(luku.id), "account_number": "12345678", "amount": "1000.00",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["token_or_receipt"]
        assert response.data["token_or_receipt"].startswith("MOCK-")

    def test_insufficient_balance_rejected_and_no_bill_payment_completed(self, luku, buyer):
        buyer.wallet.balance = Decimal("100.00")
        buyer.wallet.save(update_fields=["balance"])
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(PAYMENTS_URL, {
            "biller": str(luku.id), "account_number": "12345678", "amount": "1000.00",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        buyer.wallet.refresh_from_db()
        assert buyer.wallet.balance == Decimal("100.00")

        bill_payment = BillPayment.objects.get(user=buyer)
        assert bill_payment.status == BillPaymentStatus.FAILED

    def test_biller_failure_refunds_wallet(self, luku, buyer):
        api = APIClient()
        api.force_authenticate(user=buyer)
        with patch("billpay.views.bill_payment_views.purchase") as mock_purchase:
            mock_purchase.return_value = {"status": "failed", "error": "Biller haipatikani."}
            response = api.post(PAYMENTS_URL, {
                "biller": str(luku.id), "account_number": "12345678", "amount": "1000.00",
            }, format="json")

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

        buyer.wallet.refresh_from_db()
        assert buyer.wallet.balance == Decimal("50000.00")  # fully refunded

        bill_payment = BillPayment.objects.get(user=buyer)
        assert bill_payment.status == BillPaymentStatus.FAILED
        txns = Transaction.objects.filter(wallet=buyer.wallet).order_by("created_at")
        assert [t.transaction_type for t in txns] == [
            Transaction.TransactionType.WITHDRAWAL, Transaction.TransactionType.REFUND,
        ]

    def test_inactive_biller_rejected(self, tz, buyer):
        inactive = Biller.objects.create(
            name="Old Biller", category=BillerCategory.WATER, country=tz, config_key="TZ_WATER", is_active=False,
        )
        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(PAYMENTS_URL, {
            "biller": str(inactive.id), "account_number": "12345678", "amount": "1000.00",
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_sees_only_own_bill_payments(self, luku, buyer, user_factory):
        other = user_factory(role="CLIENT")
        other.is_identity_verified = True
        other.is_phone_verified = True
        other.save(update_fields=["is_identity_verified", "is_phone_verified"])
        other.wallet.balance = Decimal("10000.00")
        other.wallet.save(update_fields=["balance"])

        api = APIClient()
        api.force_authenticate(user=other)
        api.post(PAYMENTS_URL, {"biller": str(luku.id), "account_number": "99999999", "amount": "500.00"}, format="json")

        api.force_authenticate(user=buyer)
        response = api.get(PAYMENTS_URL)
        data = response.data if isinstance(response.data, list) else response.data["results"]
        assert data == []
