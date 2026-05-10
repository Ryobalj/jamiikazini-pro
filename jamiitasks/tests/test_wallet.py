# jamiitasks/tests/test_wallet.py

import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.topup import TopUp
from jamiiwallet.models.transaction import Transaction

from jamiitasks.tasks.wallet import confirm_topup_transaction

User = get_user_model()


@pytest.mark.django_db
def test_confirm_topup_transaction_success(mocker):
    # 1. Tengeneza mtumiaji na wallet
    user = User.objects.create_user(username='client1', email='client@example.com', password='pass')
    wallet = Wallet.objects.create(user=user, balance=Decimal('100.00'), currency='TZS')

    # 2. Tengeneza TopUp
    topup = TopUp.objects.create(
        wallet=wallet,
        user=user,
        amount=Decimal('50.00'),
        status=TopUp.TopUpStatus.PENDING,
        reference='TX12345',
        metadata={'gateway': 'simulated'},
        initiated_at=timezone.now(),
    )

    # 3. Hakikisha balance ya awali
    assert wallet.balance == Decimal('100.00')
    assert Transaction.objects.count() == 0

    # 4. Simulate external confirmation always successful
    mocker.patch('jamiitasks.tasks.wallet.simulate_payment_gateway_confirmation', return_value=True)

    # 5. Run celery task directly
    result = confirm_topup_transaction(topup.id)

    # 6. Refresh from DB
    wallet.refresh_from_db()
    topup.refresh_from_db()

    # 7. Assert balance and status
    assert wallet.balance == Decimal('150.00')
    assert topup.status == TopUp.TopUpStatus.CONFIRMED
    assert Transaction.objects.count() == 1

    txn = Transaction.objects.first()
    assert txn.amount == topup.amount
    assert txn.reference == topup.reference

    assert "confirmed" in result.lower()