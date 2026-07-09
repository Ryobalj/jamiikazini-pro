# payments/tests/test_wallet_bridge.py

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from payments.wallet_bridge import WalletBridge
from jamiitasks.tasks.payment_tasks import notify_wallet_balance_change
from jamiiwallet.models.wallet import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()


# -------------------- Fixtures -------------------- #

@pytest.fixture
def dummy_transaction():
    class DummyTransaction:
        pass
    return DummyTransaction()


@pytest.fixture
def mock_transaction_engine(monkeypatch, dummy_transaction):
    def mock_initiate(**kwargs):
        if kwargs.get("amount") == Decimal("0.00"):
            raise ValidationError("Invalid amount")
        return dummy_transaction

    def mock_process(transaction):
        return transaction

    monkeypatch.setattr(
        "jamiiwallet.services.transaction_engine.TransactionEngine.initiate",
        mock_initiate
    )
    monkeypatch.setattr(
        "jamiiwallet.services.transaction_engine.TransactionEngine.process",
        mock_process
    )
    return dummy_transaction


@pytest.fixture
def user_with_wallet(user_factory, wallet_factory):
    """Returns a user with an active wallet."""
    user = user_factory()
    wallet_factory(user=user)
    return user


# -------------------- Wallet Bridge Tests -------------------- #

@pytest.mark.django_db
def test_top_up_wallet_success(user_with_wallet, mock_transaction_engine):
    tx = WalletBridge.top_up_wallet(user=user_with_wallet, amount=Decimal("100.00"))
    assert isinstance(tx, type(mock_transaction_engine))


@pytest.mark.django_db
def test_withdraw_from_wallet_success(user_with_wallet, mock_transaction_engine):
    tx = WalletBridge.withdraw_from_wallet(user=user_with_wallet, amount=Decimal("50.00"))
    assert isinstance(tx, type(mock_transaction_engine))


@pytest.mark.django_db
def test_transfer_between_wallets_success(user_factory, wallet_factory, mock_transaction_engine):
    sender = user_factory()
    recipient = user_factory()
    wallet_factory(user=sender)
    recipient_wallet = wallet_factory(user=recipient)
    tx = WalletBridge.transfer_between_wallets(
        sender=sender,
        recipient_wallet_id=recipient_wallet.id,
        amount=Decimal("25.00")
    )
    assert isinstance(tx, type(mock_transaction_engine))


def test_wallet_not_found_raises_error(monkeypatch, mock_transaction_engine):
    monkeypatch.setattr(
        "jamiiwallet.models.wallet.Wallet.objects.get",
        lambda **kwargs: (_ for _ in ()).throw(Exception("Wallet not found"))
    )
    with pytest.raises(Exception, match="Wallet not found"):
        WalletBridge.top_up_wallet(user="user1", amount=Decimal("100.00"))


@pytest.mark.django_db
def test_initiate_raises_validation_error(user_with_wallet, monkeypatch):
    monkeypatch.setattr(
        "jamiiwallet.services.transaction_engine.TransactionEngine.initiate",
        lambda **kwargs: (_ for _ in ()).throw(ValidationError("Invalid amount")),
    )
    with pytest.raises(ValidationError, match="Invalid amount"):
        WalletBridge.top_up_wallet(user=user_with_wallet, amount=Decimal("0.00"))


# -------------------- Task Tests -------------------- #

@pytest.mark.django_db
def test_notify_wallet_balance_change_logs_and_completes(caplog, user_with_wallet):
    wallet = Wallet.objects.get(user=user_with_wallet)
    new_balance = Decimal("150.00")

    with caplog.at_level("INFO"):
        result = notify_wallet_balance_change(wallet.id, user_with_wallet.id, new_balance)

    assert f"Balance change for wallet {wallet.id}" in caplog.text
    assert result is True  # Badilisha hapa kutoka None kwenda True

# -------------------- Signal Tests -------------------- #

@pytest.fixture
def _reconnect_wallet_signal():
    """Vipimo hivi vinapima signal ya auto-create wallet ambayo root conftest
    huikata - iunganishe tena kwa vipimo hivi tu."""
    from django.db.models.signals import post_save
    from jamiiwallet.signals import create_or_reactivate_wallet
    post_save.connect(create_or_reactivate_wallet, sender=User)
    yield
    post_save.disconnect(create_or_reactivate_wallet, sender=User)


@pytest.mark.django_db
def test_create_wallet_on_user_creation(user_factory, _reconnect_wallet_signal):
    user = user_factory()
    wallet = Wallet.objects.filter(user=user).first()
    assert wallet is not None
    assert wallet.is_active is True


@pytest.mark.django_db
def test_reactivate_wallet_on_user_save(user_factory, _reconnect_wallet_signal):
    user = user_factory()
    wallet, created = Wallet.objects.get_or_create(user=user)
    wallet.is_active = False
    wallet.save()

    user.full_name = "Changed Name"
    user.save()
    wallet.refresh_from_db()

    assert wallet.is_active is True


@pytest.mark.django_db
def test_create_wallet_if_missing_on_user_save(user_factory, _reconnect_wallet_signal):
    user = user_factory()
    Wallet.objects.filter(user=user).delete()
    user.full_name = "New Name"
    user.save()
    wallet = Wallet.objects.filter(user=user).first()
    assert wallet is not None