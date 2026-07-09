# payments/tests/test_tasks.py

import pytest
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model

from jamiitasks.tasks.payment_tasks import (
    process_payment,
    retry_failed_topups,
    notify_wallet_balance_change,
)
from payments.models.payment_failure import PaymentFailure
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user_with_wallet(user_factory, wallet_factory):
    user = user_factory()
    wallet_factory(user=user, balance=Decimal("100.00"))
    return user


@pytest.fixture
def user(user_factory):
    return user_factory()


class TestProcessPayment:
    """Test cases for process_payment task"""
    
    def test_process_payment_success(self, user_with_wallet):
        """Test successful payment processing when balance is enough."""
        user = user_with_wallet
        amount = Decimal("50.00")
        reference = "REF12345"

        result = process_payment.run(user.id, amount, reference)
        wallet = Wallet.objects.get(user=user)

        assert result["success"] is True
        assert result["type"] == "standard"
        assert wallet.balance == Decimal("50.00")

    def test_process_payment_insufficient_balance_retries(self, user_with_wallet):
        """Test payment retry logic for insufficient balance."""
        user = user_with_wallet
        amount = Decimal("200.00")
        reference = "REF_FAIL_TEST"

        # push_request ndiyo njia rasmi ya celery kuweka request context kwenye tests
        # (kupatch property 'request' kunavunjika - haina setter/deleter)
        process_payment.push_request(retries=0, id="test-retry")
        try:
            with patch.object(process_payment, 'retry') as mock_retry:
                mock_retry.side_effect = Exception("Retry called")

                with pytest.raises(Exception, match="Retry called"):
                    process_payment.run(user.id, amount, reference)

                # Verify retry was attempted (huweza kuitwa tena kwenye except-block)
                assert mock_retry.call_count >= 1
        finally:
            process_payment.pop_request()

    def test_process_payment_max_retries_exceeded(self, user_with_wallet):
        """Test payment failure after max retries exceeded."""
        user = user_with_wallet
        amount = Decimal("200.00")
        reference = "REF_MAX_RETRIES"

        # retries zimezidi max_retries (5) - retry() itatupa MaxRetriesExceededError
        process_payment.push_request(retries=99, id="test-max-retries")
        try:
            result = process_payment.run(user.id, amount, reference)
        finally:
            process_payment.pop_request()

        assert result["success"] is False
        assert result["type"] == "standard"

        # Verify PaymentFailure record was created
        assert PaymentFailure.objects.filter(
            user_id=user.id,
            reference=reference
        ).exists()


class TestRetryFailedTopups:
    """Test cases for retry_failed_topups task"""
    
    def test_retry_failed_topups_success(self, user, wallet_factory):
        """Test retrying failed top-up transactions."""
        wallet = wallet_factory(user=user, balance=Decimal("0.00"))
        unique_ref = f"TXN_FAILED_{uuid.uuid4().hex[:8]}"
        
        # Create a failed transaction
        txn = Transaction.objects.create(
            wallet=wallet,
            transaction_type=Transaction.TransactionType.TOP_UP,
            status=Transaction.TransactionStatus.FAILED,
            reference=unique_ref,
            amount=Decimal("10.00"),
            initiated_by=user
        )

        # Mock the TransactionEngine.process method
        with patch.object(TransactionEngine, 'process') as mock_process:
            mock_process.return_value = None
            
            result = retry_failed_topups()
            
            # Verify the transaction was processed
            mock_process.assert_called_once()
            assert result == "Retried 1 failed top-up(s)."

    def test_retry_failed_topups_with_exception(self, user, wallet_factory, caplog):
        """Test retry_failed_topups handles exceptions gracefully."""
        wallet = wallet_factory(user=user, balance=Decimal("0.00"))
        unique_ref = f"TXN_FAILED_{uuid.uuid4().hex[:8]}"
        
        # Create a failed transaction
        Transaction.objects.create(
            wallet=wallet,
            transaction_type=Transaction.TransactionType.TOP_UP,
            status=Transaction.TransactionStatus.FAILED,
            reference=unique_ref,
            amount=Decimal("10.00"),
            initiated_by=user
        )

        # Mock TransactionEngine.process to raise an exception
        with patch.object(TransactionEngine, 'process') as mock_process:
            mock_process.side_effect = Exception("Processing failed")
            
            with caplog.at_level("WARNING"):
                result = retry_failed_topups()
            
            # Verify the task completed but logged the error
            assert "Could not retry" in caplog.text
            assert result == "Retried 0 failed top-up(s)."

    def test_retry_failed_topups_no_failed_transactions(self):
        """Test retry_failed_topups when there are no failed transactions."""
        result = retry_failed_topups()
        assert result == "Retried 0 failed top-up(s)."


class TestNotifyWalletBalanceChange:
    """Test cases for notify_wallet_balance_change task"""
    
    def test_notify_wallet_balance_change_success(self, user_with_wallet, caplog):
        """Test that wallet balance change task logs the update."""
        wallet = Wallet.objects.get(user=user_with_wallet)
        new_balance = Decimal("150.00")

        with caplog.at_level("INFO"):
            result = notify_wallet_balance_change.run(
                wallet.id, 
                user_with_wallet.id, 
                new_balance
            )

        assert "Balance change for wallet" in caplog.text
        assert str(wallet.id) in caplog.text
        assert str(user_with_wallet.id) in caplog.text
        assert str(new_balance) in caplog.text
        assert result is True

    def test_notify_wallet_balance_change_retry_on_exception(self):
        """Test that the task retries on exception."""
        wallet_id = 999  # Non-existent wallet
        user_id = 888    # Non-existent user
        new_balance = Decimal("150.00")

        with patch('jamiitasks.tasks.payment_tasks.notify_wallet_balance_change.retry') as mock_retry:
            mock_retry.side_effect = Exception("Retry called")

            # Lazimisha exception ndani ya try block tu (SUCCESS hutokea ndani ya try)
            def _boom(task_name, task_id, payload, status, extra=None):
                if status == "SUCCESS":
                    raise RuntimeError("boom")

            with patch('jamiitasks.tasks.payment_tasks._safe_log_execution', side_effect=_boom):
                with pytest.raises(Exception, match="Retry called"):
                    notify_wallet_balance_change.run(wallet_id, user_id, new_balance)

            # Verify retry was called
            mock_retry.assert_called_once()


class TestPaymentFailureIntegration:
    """Integration tests for payment failure handling"""
    
    def test_payment_failure_creation_on_max_retries(self, user_with_wallet):
        """Test that PaymentFailure record is created when max retries exceeded."""
        user = user_with_wallet
        amount = Decimal("200.00")
        reference = "REF_INTEGRATION_TEST"
        
        # Ensure no existing failure record
        PaymentFailure.objects.filter(reference=reference).delete()
        
        # Trigger the task with insufficient balance to cause failure
        # retries zimezidi max_retries (5) - retry() itatupa MaxRetriesExceededError
        process_payment.push_request(retries=99, id="test-integration-max")
        try:
            result = process_payment.run(user.id, amount, reference)
        finally:
            process_payment.pop_request()

        # Verify the result
        assert result["success"] is False

        # Verify PaymentFailure was created with correct data
        failure = PaymentFailure.objects.get(reference=reference)
        assert failure.user_id == user.id
        assert failure.amount == amount
        assert failure.retries == 5
        assert "Insufficient balance" in failure.reason