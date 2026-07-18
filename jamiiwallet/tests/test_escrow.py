# jamiiwallet/tests/test_escrow.py

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from payments.models.currency import Currency
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine

User = get_user_model()


@pytest.fixture
def currency(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def payer(db, currency):
    user = User.objects.create_user(email="payer@example.com", password="testpass", full_name="Payer P")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("1000.00"), "currency": currency})
    return user


@pytest.fixture
def seller(db, currency):
    user = User.objects.create_user(email="seller@example.com", password="testpass", full_name="Seller S")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


@pytest.fixture
def driver(db, currency):
    user = User.objects.create_user(email="driver@example.com", password="testpass", full_name="Driver D")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


def _run(**kwargs):
    txn = TransactionEngine.initiate(**kwargs)
    return TransactionEngine.process(txn)


@pytest.mark.django_db
def test_hold_reduces_available_balance_not_balance(payer):
    _run(wallet=payer.wallet, amount=Decimal("300.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)

    payer.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("1000.00")
    assert payer.wallet.held_balance == Decimal("300.00")
    assert payer.wallet.available_balance == Decimal("700.00")


@pytest.mark.django_db
def test_hold_fails_cleanly_when_insufficient_available_balance(payer):
    with pytest.raises(ValidationError):
        _run(wallet=payer.wallet, amount=Decimal("5000.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)

    payer.wallet.refresh_from_db()
    assert payer.wallet.held_balance == Decimal("0.00")
    assert payer.wallet.balance == Decimal("1000.00")


@pytest.mark.django_db
def test_capture_moves_money_and_reduces_held_balance(payer, seller):
    _run(wallet=payer.wallet, amount=Decimal("300.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)
    _run(
        wallet=payer.wallet, amount=Decimal("300.00"), transaction_type=Transaction.TransactionType.CAPTURE,
        initiated_by=payer, counterparty=seller,
    )

    payer.wallet.refresh_from_db()
    seller.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("700.00")
    assert payer.wallet.held_balance == Decimal("0.00")
    assert seller.wallet.balance == Decimal("300.00")


@pytest.mark.django_db
def test_two_partial_captures_against_one_hold_net_to_zero(payer, seller, driver):
    # Mirrors the real order flow: one HOLD covers both product + delivery,
    # then two separate CAPTUREs (seller + driver) drain it exactly.
    _run(wallet=payer.wallet, amount=Decimal("500.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)

    _run(
        wallet=payer.wallet, amount=Decimal("400.00"), transaction_type=Transaction.TransactionType.CAPTURE,
        initiated_by=payer, counterparty=seller,
    )
    _run(
        wallet=payer.wallet, amount=Decimal("100.00"), transaction_type=Transaction.TransactionType.CAPTURE,
        initiated_by=payer, counterparty=driver,
    )

    payer.wallet.refresh_from_db()
    seller.wallet.refresh_from_db()
    driver.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("500.00")
    assert payer.wallet.held_balance == Decimal("0.00")
    assert seller.wallet.balance == Decimal("400.00")
    assert driver.wallet.balance == Decimal("100.00")


@pytest.mark.django_db
def test_void_fully_releases_hold_with_no_balance_change(payer):
    _run(wallet=payer.wallet, amount=Decimal("300.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)
    _run(wallet=payer.wallet, amount=Decimal("300.00"), transaction_type=Transaction.TransactionType.VOID, initiated_by=payer)

    payer.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("1000.00")
    assert payer.wallet.held_balance == Decimal("0.00")
    assert payer.wallet.available_balance == Decimal("1000.00")


@pytest.mark.django_db
def test_capture_fails_when_amount_exceeds_held_balance(payer, seller):
    _run(wallet=payer.wallet, amount=Decimal("100.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)

    with pytest.raises(ValidationError):
        _run(
            wallet=payer.wallet, amount=Decimal("200.00"), transaction_type=Transaction.TransactionType.CAPTURE,
            initiated_by=payer, counterparty=seller,
        )


@pytest.mark.django_db
def test_void_fails_when_amount_exceeds_held_balance(payer):
    _run(wallet=payer.wallet, amount=Decimal("100.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)

    with pytest.raises(ValidationError):
        _run(wallet=payer.wallet, amount=Decimal("200.00"), transaction_type=Transaction.TransactionType.VOID, initiated_by=payer)


@pytest.mark.django_db
def test_active_hold_blocks_spending_the_held_portion_via_withdrawal(payer):
    _run(wallet=payer.wallet, amount=Decimal("800.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)

    # Only 200.00 is actually spendable now, even though balance still shows 1000.00.
    with pytest.raises(ValidationError):
        _run(wallet=payer.wallet, amount=Decimal("300.00"), transaction_type=Transaction.TransactionType.WITHDRAWAL, initiated_by=payer)

    payer.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("1000.00")
    assert payer.wallet.held_balance == Decimal("800.00")


@pytest.mark.django_db
def test_active_hold_blocks_spending_the_held_portion_via_payment(payer, seller):
    _run(wallet=payer.wallet, amount=Decimal("800.00"), transaction_type=Transaction.TransactionType.HOLD, initiated_by=payer)

    with pytest.raises(ValidationError):
        _run(
            wallet=payer.wallet, amount=Decimal("300.00"), transaction_type=Transaction.TransactionType.PAYMENT,
            initiated_by=payer, counterparty=seller,
        )

    payer.wallet.refresh_from_db()
    seller.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("1000.00")
    assert seller.wallet.balance == Decimal("0.00")
