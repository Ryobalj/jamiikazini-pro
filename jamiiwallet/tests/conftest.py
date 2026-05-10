import pytest
from decimal import Decimal
from jamiiwallet.models.wallet import Wallet

@pytest.fixture
def wallet_factory(db):
    def create_wallet(user, **kwargs):
        defaults = {
            "balance": Decimal("0.00"),
            "is_active": True,
        }
        defaults.update(kwargs)
        wallet, created = Wallet.objects.get_or_create(user=user, defaults=defaults)
        return wallet
    return create_wallet