# jamiiwallet/tests/test_payment_request.py

import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from payments.models.currency import Currency
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.payment_request import PaymentRequest
from jamiiwallet.models.transfer import Transfer

User = get_user_model()


@pytest.fixture
def currency(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def requester(db, currency):
    user = User.objects.create_user(email="requester@example.com", password="testpass", full_name="Requester Q")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


@pytest.fixture
def payer(db, currency):
    user = User.objects.create_user(email="payer@example.com", password="testpass", full_name="Payer P")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("500.00"), "currency": currency})
    return user


@pytest.mark.django_db
def test_create_payment_request(requester, payer):
    client = APIClient()
    client.force_authenticate(user=requester)

    response = client.post(
        reverse('wallet:payment-request-list'),
        {"amount": "200.00", "payer_identifier": "payer@example.com", "note": "deni"},
        format='json',
    )

    assert response.status_code == 201, response.content
    data = response.json()
    assert data["status"] == PaymentRequest.RequestStatus.PENDING
    assert data["direction"] == "outgoing"
    assert data["payer_name"] == "Payer P"


@pytest.mark.django_db
def test_payer_accepts_request_creates_transfer(requester, payer):
    pr = PaymentRequest.objects.create(requester=requester, payer=payer, amount=Decimal("200.00"))

    client = APIClient()
    client.force_authenticate(user=payer)
    response = client.post(reverse('wallet:payment-request-accept', args=[pr.id]))

    assert response.status_code == 200, response.content
    pr.refresh_from_db()
    assert pr.status == PaymentRequest.RequestStatus.ACCEPTED
    assert pr.resulting_transfer is not None
    assert pr.resulting_transfer.status == Transfer.TransferStatus.COMPLETED

    requester.wallet.refresh_from_db()
    payer.wallet.refresh_from_db()
    assert requester.wallet.balance == Decimal("200.00")
    assert payer.wallet.balance == Decimal("300.00")


@pytest.mark.django_db
def test_only_payer_can_accept(requester, payer):
    pr = PaymentRequest.objects.create(requester=requester, payer=payer, amount=Decimal("50.00"))

    client = APIClient()
    client.force_authenticate(user=requester)  # requester, not payer, tries to accept
    response = client.post(reverse('wallet:payment-request-accept', args=[pr.id]))

    assert response.status_code == 403
    pr.refresh_from_db()
    assert pr.status == PaymentRequest.RequestStatus.PENDING


@pytest.mark.django_db
def test_payer_declines_request(requester, payer):
    pr = PaymentRequest.objects.create(requester=requester, payer=payer, amount=Decimal("50.00"))

    client = APIClient()
    client.force_authenticate(user=payer)
    response = client.post(reverse('wallet:payment-request-decline', args=[pr.id]))

    assert response.status_code == 200
    pr.refresh_from_db()
    assert pr.status == PaymentRequest.RequestStatus.DECLINED
    payer.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("500.00")  # haijabadilika


@pytest.mark.django_db
def test_accept_fails_when_payer_balance_insufficient(requester, payer):
    pr = PaymentRequest.objects.create(requester=requester, payer=payer, amount=Decimal("5000.00"))

    client = APIClient()
    client.force_authenticate(user=payer)
    response = client.post(reverse('wallet:payment-request-accept', args=[pr.id]))

    assert response.status_code == 400
    pr.refresh_from_db()
    assert pr.status == PaymentRequest.RequestStatus.PENDING  # bado inasubiri, si ACCEPTED
    payer.wallet.refresh_from_db()
    assert payer.wallet.balance == Decimal("500.00")


@pytest.mark.django_db
def test_list_shows_incoming_and_outgoing(requester, payer):
    PaymentRequest.objects.create(requester=requester, payer=payer, amount=Decimal("10.00"))
    PaymentRequest.objects.create(requester=payer, payer=requester, amount=Decimal("20.00"))

    client = APIClient()
    client.force_authenticate(user=requester)
    response = client.get(reverse('wallet:payment-request-list'))

    assert response.status_code == 200
    body = response.json()
    results = body.get("results", body) if isinstance(body, dict) else body
    assert len(results) == 2
    directions = {r["direction"] for r in results}
    assert directions == {"outgoing", "incoming"}
