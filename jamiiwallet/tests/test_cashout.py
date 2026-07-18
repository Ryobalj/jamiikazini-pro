# jamiiwallet/tests/test_cashout.py

import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from payments.models.currency import Currency
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.transfer import Transfer
from businesses.models.business import Business

User = get_user_model()


@pytest.fixture
def currency(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def buyer(db, currency):
    user = User.objects.create_user(email="cashout-buyer@example.com", password="testpass", full_name="Buyer B")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("1000.00"), "currency": currency})
    return user


@pytest.fixture
def shop_owner(db, currency):
    user = User.objects.create_user(email="cashout-owner@example.com", password="testpass", full_name="Owner O")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


@pytest.fixture
def verified_business(db, shop_owner):
    return Business.objects.create(owner=shop_owner, name="Verified Shop", is_verified=True)


@pytest.mark.django_db
def test_cashout_moves_balance_with_no_fee(buyer, shop_owner, verified_business):
    client = APIClient()
    client.force_authenticate(user=buyer)

    response = client.post(
        reverse('wallet:cash-out'),
        {"amount": "300.00", "business_id": str(verified_business.id), "note": "haja ya pesa taslimu"},
        format='json',
    )

    assert response.status_code == 201, response.content
    data = response.json()
    assert data["status"] == Transfer.TransferStatus.COMPLETED
    assert data["business_name"] == "Owner O"

    buyer.wallet.refresh_from_db()
    shop_owner.wallet.refresh_from_db()
    # No fee: exactly 300 debited, exactly 300 credited.
    assert buyer.wallet.balance == Decimal("700.00")
    assert shop_owner.wallet.balance == Decimal("300.00")

    transfer = Transfer.objects.get(id=data["id"])
    assert transfer.amount == Decimal("300.00")
    assert "Verified Shop" in transfer.note


@pytest.mark.django_db
def test_cashout_rejected_for_unverified_business(buyer, shop_owner, currency):
    unverified_business = Business.objects.create(owner=shop_owner, name="Unverified Shop", is_verified=False)
    client = APIClient()
    client.force_authenticate(user=buyer)

    response = client.post(
        reverse('wallet:cash-out'),
        {"amount": "100.00", "business_id": str(unverified_business.id)},
        format='json',
    )

    assert response.status_code == 400
    assert Transfer.objects.count() == 0
    buyer.wallet.refresh_from_db()
    assert buyer.wallet.balance == Decimal("1000.00")


@pytest.mark.django_db
def test_cashout_rejected_when_balance_insufficient(buyer, verified_business):
    client = APIClient()
    client.force_authenticate(user=buyer)

    response = client.post(
        reverse('wallet:cash-out'),
        {"amount": "5000.00", "business_id": str(verified_business.id)},
        format='json',
    )

    assert response.status_code == 400
    assert Transfer.objects.count() == 0


@pytest.mark.django_db
def test_cashout_rejected_for_own_business(buyer, currency):
    own_business = Business.objects.create(owner=buyer, name="My Own Shop", is_verified=True)
    client = APIClient()
    client.force_authenticate(user=buyer)

    response = client.post(
        reverse('wallet:cash-out'),
        {"amount": "50.00", "business_id": str(own_business.id)},
        format='json',
    )

    assert response.status_code == 400
    assert Transfer.objects.count() == 0


@pytest.mark.django_db
def test_cashout_rejected_for_nonexistent_business(buyer):
    client = APIClient()
    client.force_authenticate(user=buyer)

    response = client.post(
        reverse('wallet:cash-out'),
        {"amount": "50.00", "business_id": "00000000-0000-0000-0000-000000000000"},
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_cashout_requires_authentication(verified_business):
    client = APIClient()
    response = client.post(
        reverse('wallet:cash-out'),
        {"amount": "50.00", "business_id": str(verified_business.id)},
        format='json',
    )
    assert response.status_code == 401
