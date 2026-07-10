# jamiiwallet/tests/test_topup_views.py

import pytest
from payments.models.currency import Currency
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.topup import TopUp

User = get_user_model()

@pytest.mark.django_db
def test_topup_view_creates_topup_and_calls_task(mocker):
    client = APIClient()

    # 1. Tengeneza mtumiaji na wallet
    user = User.objects.create_user(
        email='client@example.com',
        password='testpass'
    )
    wallet, _ = Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal('0.00'), "currency": Currency.objects.get_or_create(code="TZS")[0]})

    client.force_authenticate(user=user)

    # 2. Mock celery task
    mock_task = mocker.patch(
        'jamiiwallet.views.topup_views.confirm_topup_transaction.delay',
        return_value=None
    )

    # 3. Data ya topup (PawaPay inahitaji mno + phone)
    data = {
        'amount': '150.00',
        'channel': 'pawapay',
        'mno': 'airtel',
        'phone': '+255783456789',
        'metadata': {
            'payment_method': 'm-pesa',
            'reference': 'MPESA123456'
        }
    }

    # 4. Tuma request
    response = client.post(reverse('wallet:topup'), data, format='json')

    # 5. Assert response
    assert response.status_code == 201
    response_data = response.json()
    assert 'id' in response_data
    assert Decimal(str(response_data['amount'])) == Decimal('150.00')
    assert response_data['status'] == TopUp.TopUpStatus.INITIATED
    assert 'created_at' in response_data

    # 6. Assert topup imeundwa kwenye database
    topup = TopUp.objects.get(id=response_data['id'])
    assert topup.amount == Decimal('150.00')
    assert topup.user == user
    assert topup.channel == 'pawapay'
    assert topup.provider == 'AIRTEL_TZA'   # mno 'airtel' -> PawaPay code
    assert topup.phone == '255783456789'    # normalized MSISDN (no +)

    # 7. Assert celery task ilitumwa
    mock_task.assert_called_once_with(str(topup.id))