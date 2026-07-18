# jamiiwallet/tests/test_escrow_hold.py

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from payments.models.currency import Currency
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.escrow_hold import EscrowHold, EscrowHoldStatus
from jamiiwallet.services.escrow_hold_service import open_hold, capture_from_hold, void_remaining

User = get_user_model()


@pytest.fixture
def currency(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def payer(db, currency):
    user = User.objects.create_user(email="eh-payer@example.com", password="testpass", full_name="Payer P")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("1000.00"), "currency": currency})
    return user


@pytest.fixture
def contractor(db, currency):
    user = User.objects.create_user(email="eh-contractor@example.com", password="testpass", full_name="Contractor C")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


@pytest.fixture
def driver(db, currency):
    user = User.objects.create_user(email="eh-driver@example.com", password="testpass", full_name="Driver D")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


@pytest.mark.django_db
class TestOpenHold:
    def test_open_hold_creates_escrow_and_holds_wallet_balance(self, payer):
        eh = open_hold(payer.wallet, Decimal("500.00"), initiated_by=payer)

        payer.wallet.refresh_from_db()
        assert eh.total_held == Decimal("500.00")
        assert eh.remaining == Decimal("500.00")
        assert eh.status == EscrowHoldStatus.OPEN
        assert payer.wallet.held_balance == Decimal("500.00")
        assert payer.wallet.balance == Decimal("1000.00")

    def test_open_hold_links_generic_object(self, payer, business_factory):
        business = business_factory(owner=payer)
        eh = open_hold(payer.wallet, Decimal("200.00"), initiated_by=payer, linked_object=business)

        assert eh.linked_object == business

    def test_open_hold_insufficient_balance_raises(self, payer):
        with pytest.raises(ValidationError):
            open_hold(payer.wallet, Decimal("5000.00"), initiated_by=payer)
        assert not EscrowHold.objects.filter(wallet=payer.wallet).exists()

    def test_open_hold_rejects_non_positive_amount(self, payer):
        with pytest.raises(ValidationError):
            open_hold(payer.wallet, Decimal("0.00"), initiated_by=payer)


@pytest.mark.django_db
class TestCaptureFromHold:
    def test_partial_capture_updates_totals_and_pays_counterparty(self, payer, contractor):
        eh = open_hold(payer.wallet, Decimal("1000.00"), initiated_by=payer)

        capture_from_hold(eh, Decimal("300.00"), counterparty=contractor, initiated_by=payer)

        eh.refresh_from_db()
        contractor.wallet.refresh_from_db()
        assert eh.total_captured == Decimal("300.00")
        assert eh.remaining == Decimal("700.00")
        assert eh.status == EscrowHoldStatus.OPEN
        assert contractor.wallet.balance == Decimal("300.00")

    def test_multiple_milestone_captures_sum_correctly_and_autoclose(self, payer, contractor):
        eh = open_hold(payer.wallet, Decimal("900.00"), initiated_by=payer)

        capture_from_hold(eh, Decimal("300.00"), counterparty=contractor, initiated_by=payer)
        capture_from_hold(eh, Decimal("300.00"), counterparty=contractor, initiated_by=payer)
        capture_from_hold(eh, Decimal("300.00"), counterparty=contractor, initiated_by=payer)

        eh.refresh_from_db()
        payer.wallet.refresh_from_db()
        contractor.wallet.refresh_from_db()
        assert eh.total_captured == Decimal("900.00")
        assert eh.remaining == Decimal("0.00")
        assert eh.status == EscrowHoldStatus.CLOSED
        assert payer.wallet.held_balance == Decimal("0.00")
        assert contractor.wallet.balance == Decimal("900.00")

    def test_split_capture_to_two_counterparties(self, payer, contractor, driver):
        eh = open_hold(payer.wallet, Decimal("500.00"), initiated_by=payer)

        capture_from_hold(eh, Decimal("400.00"), counterparty=contractor, initiated_by=payer)
        capture_from_hold(eh, Decimal("100.00"), counterparty=driver, initiated_by=payer)

        eh.refresh_from_db()
        contractor.wallet.refresh_from_db()
        driver.wallet.refresh_from_db()
        assert eh.remaining == Decimal("0.00")
        assert eh.status == EscrowHoldStatus.CLOSED
        assert contractor.wallet.balance == Decimal("400.00")
        assert driver.wallet.balance == Decimal("100.00")

    def test_capture_rejects_amount_exceeding_remaining(self, payer, contractor):
        eh = open_hold(payer.wallet, Decimal("300.00"), initiated_by=payer)

        with pytest.raises(ValidationError):
            capture_from_hold(eh, Decimal("301.00"), counterparty=contractor, initiated_by=payer)

        eh.refresh_from_db()
        assert eh.total_captured == Decimal("0.00")
        assert eh.status == EscrowHoldStatus.OPEN

    def test_capture_rejects_when_hold_already_closed(self, payer, contractor):
        eh = open_hold(payer.wallet, Decimal("100.00"), initiated_by=payer)
        capture_from_hold(eh, Decimal("100.00"), counterparty=contractor, initiated_by=payer)
        eh.refresh_from_db()
        assert eh.status == EscrowHoldStatus.CLOSED

        with pytest.raises(ValidationError):
            capture_from_hold(eh, Decimal("1.00"), counterparty=contractor, initiated_by=payer)

    def test_idempotency_key_prevents_double_capture(self, payer, contractor):
        eh = open_hold(payer.wallet, Decimal("500.00"), initiated_by=payer)

        key = "milestone-capture-1"
        capture_from_hold(eh, Decimal("200.00"), counterparty=contractor, initiated_by=payer, idempotency_key=key)
        # Simulate a retried/duplicate request with the same idempotency key.
        capture_from_hold(eh, Decimal("200.00"), counterparty=contractor, initiated_by=payer, idempotency_key=key)

        eh.refresh_from_db()
        contractor.wallet.refresh_from_db()
        assert eh.total_captured == Decimal("200.00")
        assert contractor.wallet.balance == Decimal("200.00")


@pytest.mark.django_db
class TestVoidRemaining:
    def test_void_remaining_releases_leftover_and_closes(self, payer, contractor):
        eh = open_hold(payer.wallet, Decimal("1000.00"), initiated_by=payer)
        capture_from_hold(eh, Decimal("300.00"), counterparty=contractor, initiated_by=payer)

        void_remaining(eh, initiated_by=payer)

        eh.refresh_from_db()
        payer.wallet.refresh_from_db()
        assert eh.total_voided == Decimal("700.00")
        assert eh.remaining == Decimal("0.00")
        assert eh.status == EscrowHoldStatus.CLOSED
        assert payer.wallet.held_balance == Decimal("0.00")
        # 300 already left balance via capture; void only releases the hold,
        # it never moves balance - so payer keeps the un-captured 700.
        assert payer.wallet.balance == Decimal("700.00")

    def test_void_remaining_noop_when_already_closed(self, payer, contractor):
        eh = open_hold(payer.wallet, Decimal("100.00"), initiated_by=payer)
        capture_from_hold(eh, Decimal("100.00"), counterparty=contractor, initiated_by=payer)
        eh.refresh_from_db()
        assert eh.status == EscrowHoldStatus.CLOSED

        result = void_remaining(eh, initiated_by=payer)
        assert result is None

    def test_void_remaining_full_hold_returns_all_funds(self, payer):
        eh = open_hold(payer.wallet, Decimal("400.00"), initiated_by=payer)

        void_remaining(eh, initiated_by=payer)

        eh.refresh_from_db()
        payer.wallet.refresh_from_db()
        assert eh.total_voided == Decimal("400.00")
        assert eh.status == EscrowHoldStatus.CLOSED
        assert payer.wallet.held_balance == Decimal("0.00")
        # HOLD/VOID never touch balance, only held_balance - nothing was
        # ever captured, so balance stays exactly what it started as.
        assert payer.wallet.balance == Decimal("1000.00")
