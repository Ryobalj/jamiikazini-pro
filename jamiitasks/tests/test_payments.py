# jamiitasks/tests/test_payments.py

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.transaction import Transaction
from jamiitasks.services import payment_gateway as pg

pytestmark = pytest.mark.django_db

@pytest.fixture
def user_wallet(user):
    wallet, _ = Wallet.objects.update_or_create(
        user=user, defaults={"balance": Decimal("100.00")}
    )
    return wallet

@pytest.fixture
def business_wallet(business_user):
    wallet, _ = Wallet.objects.update_or_create(
        user=business_user, defaults={"balance": Decimal("0.00")}
    )
    return wallet

def test_topup_creates_pending_transaction(user):
    txn = pg.initiate_topup(user, Decimal("50.00"))
    assert txn.status == Transaction.TransactionStatus.PENDING
    assert txn.amount == Decimal("50.00")
    assert txn.wallet.user == user

def test_withdraw_success(user_wallet):
    txn = pg.initiate_withdrawal(user_wallet.user, Decimal("30.00"))
    user_wallet.refresh_from_db()
    txn.refresh_from_db()
    if txn.status == Transaction.TransactionStatus.COMPLETED:
        assert user_wallet.balance == Decimal("70.00")
    else:
        assert user_wallet.balance == Decimal("100.00")

def test_withdraw_fails_with_insufficient_funds(user_wallet):
    with pytest.raises(ValidationError):
        pg.initiate_withdrawal(user_wallet.user, Decimal("1000.00"))

def test_transfer_funds_success(user_wallet, business_wallet):
    out_txn, in_txn = pg.transfer_funds(user_wallet.user, business_wallet.user, Decimal("40.00"))
    user_wallet.refresh_from_db()
    business_wallet.refresh_from_db()

    assert user_wallet.balance == Decimal("60.00")
    assert business_wallet.balance == Decimal("40.00")
    assert out_txn.status == Transaction.TransactionStatus.COMPLETED
    assert in_txn.status == Transaction.TransactionStatus.COMPLETED

def test_make_payment_success(user_wallet, business_wallet):
    txn = pg.make_payment(user_wallet.user, business_wallet, Decimal("25.00"))
    user_wallet.refresh_from_db()
    business_wallet.refresh_from_db()

    assert user_wallet.balance == Decimal("75.00")
    assert business_wallet.balance == Decimal("25.00")
    assert txn.status == Transaction.TransactionStatus.COMPLETED

def test_refund_completed_transaction(user_wallet, business_wallet):
    # 1. Pay first
    txn = pg.make_payment(user_wallet.user, business_wallet, Decimal("20.00"))
    user_wallet.refresh_from_db()
    business_wallet.refresh_from_db()

    # 2. Refund
    refund = pg.initiate_refund(txn)

    user_wallet.refresh_from_db()
    business_wallet.refresh_from_db()

    assert user_wallet.balance == Decimal("100.00")
    assert business_wallet.balance == Decimal("0.00")
    assert refund.transaction_type == Transaction.TransactionType.REFUND

def test_refund_fails_if_not_completed(user_wallet):
    txn = pg.initiate_topup(user_wallet.user, Decimal("30.00"))
    with pytest.raises(ValidationError):
        pg.initiate_refund(txn)