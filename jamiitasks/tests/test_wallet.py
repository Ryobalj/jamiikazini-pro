# jamiitasks/tests/test_wallet.py

import pytest
from payments.models.currency import Currency
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
    wallet, _ = Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal('100.00'), "currency": Currency.objects.get_or_create(code="TZS")[0]})

    # 2. Mock gateway KABLA ya create - TopUp.save() inaendesha task eagerly
    mocker.patch('jamiitasks.tasks.wallet.confirm_with_gateway', return_value=True)
    # TopUp.save() tayari inaita task hii kwa .delay() (eager); "1/m" throttle
    # basi ingezuia kuiita tena hapa chini kwa makusudi kwa ajili ya assertion.
    mocker.patch('jamiitasks.services.rate_limiter.TaskRateLimiter.allow', return_value=True)

    topup = TopUp.objects.create(
        user=user,
        amount=Decimal('50.00'),
        status=TopUp.TopUpStatus.INITIATED,
        reference='TX12345',
        metadata={'gateway': 'simulated'},
    )

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