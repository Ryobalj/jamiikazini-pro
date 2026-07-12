# jamiiwallet/tests/test_transfer.py

import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from payments.models.currency import Currency
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.transfer import Transfer
from jamiiwallet.models.transaction import Transaction
from jamiitasks.tasks.wallet import execute_transfer

User = get_user_model()


@pytest.fixture
def currency(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def sender(db, currency):
    user = User.objects.create_user(email="sender@example.com", password="testpass", full_name="Sender S")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("1000.00"), "currency": currency})
    return user


@pytest.fixture
def recipient(db, currency):
    user = User.objects.create_user(email="recipient@example.com", password="testpass", full_name="Recipient R")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


@pytest.mark.django_db
def test_transfer_view_moves_balance_between_wallets(sender, recipient):
    client = APIClient()
    client.force_authenticate(user=sender)

    response = client.post(
        reverse('wallet:transfer'),
        {"amount": "300.00", "recipient_identifier": "recipient@example.com", "note": "chakula"},
        format='json',
    )

    assert response.status_code == 201, response.content
    data = response.json()
    assert data["status"] == Transfer.TransferStatus.COMPLETED
    assert data["recipient_name"] == "Recipient R"

    sender.wallet.refresh_from_db()
    recipient.wallet.refresh_from_db()
    assert sender.wallet.balance == Decimal("700.00")
    assert recipient.wallet.balance == Decimal("300.00")

    transfer = Transfer.objects.get(id=data["id"])
    assert transfer.sender_transaction is not None
    assert transfer.recipient_transaction is not None
    assert transfer.sender_transaction.counterparty_id == recipient.id
    assert transfer.recipient_transaction.counterparty_id == sender.id

    # direction: rekodi ya mtumaji ni 'out', ya mpokeaji ni 'in'
    def _results(resp):
        body = resp.json()
        return body.get("results", body) if isinstance(body, dict) else body

    client.force_authenticate(user=sender)
    list_resp = client.get(reverse('wallet:transaction-list'))
    assert list_resp.status_code == 200
    sender_txn_data = next(
        r for r in _results(list_resp) if r["id"] == transfer.sender_transaction_id
    )
    assert sender_txn_data["direction"] == "out"
    assert sender_txn_data["counterparty_name"] == "Recipient R"

    client.force_authenticate(user=recipient)
    list_resp2 = client.get(reverse('wallet:transaction-list'))
    recipient_txn_data = next(
        r for r in _results(list_resp2) if r["id"] == transfer.recipient_transaction_id
    )
    assert recipient_txn_data["direction"] == "in"
    assert recipient_txn_data["counterparty_name"] == "Sender S"


@pytest.mark.django_db
def test_transfer_rejected_when_balance_insufficient(sender, recipient):
    client = APIClient()
    client.force_authenticate(user=sender)

    response = client.post(
        reverse('wallet:transfer'),
        {"amount": "5000.00", "recipient_identifier": "recipient@example.com"},
        format='json',
    )

    assert response.status_code == 400
    assert Transfer.objects.count() == 0
    sender.wallet.refresh_from_db()
    assert sender.wallet.balance == Decimal("1000.00")


@pytest.mark.django_db
def test_transfer_rejected_to_self(sender):
    client = APIClient()
    client.force_authenticate(user=sender)

    response = client.post(
        reverse('wallet:transfer'),
        {"amount": "10.00", "recipient_identifier": "sender@example.com"},
        format='json',
    )

    assert response.status_code == 400
    assert Transfer.objects.count() == 0


@pytest.mark.django_db
def test_execute_transfer_is_idempotent(sender, recipient):
    transfer = Transfer.objects.create(sender=sender, recipient=recipient, amount=Decimal("100.00"))
    # save() already queued+ran process_transfer_transaction once (EAGER mode)
    sender.wallet.refresh_from_db()
    recipient.wallet.refresh_from_db()
    assert sender.wallet.balance == Decimal("900.00")
    assert recipient.wallet.balance == Decimal("100.00")

    # Calling execute_transfer again must be a no-op (idempotency_key already exists)
    execute_transfer(transfer)
    sender.wallet.refresh_from_db()
    recipient.wallet.refresh_from_db()
    assert sender.wallet.balance == Decimal("900.00")
    assert recipient.wallet.balance == Decimal("100.00")
    assert Transaction.objects.count() == 2
