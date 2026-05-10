# jamiiwallet/models/wallet.py

from django.db import models
from django.conf import settings
from kiini.models.base import UUIDModel, TimeStampedModel
from payments.models.currency import Currency


def get_default_currency():
    try:
        return Currency.objects.get(code='TZS').id
    except:
        return None

class Wallet(UUIDModel, TimeStampedModel):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        limit_choices_to={'is_active': True},
        default=get_default_currency,
        related_name='wallets'
    )

    # currency = models.ForeignKey(
    #     Currency,
    #     on_delete=models.PROTECT,
    #     limit_choices_to={'is_active': True},
    #     null=True,        # ✔ no default during migration
    #     blank=True,       # ✔ allow temporary nulls
    #     related_name='wallets'
    # )

    is_active = models.BooleanField(default=True)

    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_updates'
    )

    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'

    def __str__(self):
        return f"{self.user.full_name} - {self.currency.code} {self.balance}"

    def has_sufficient_balance(self, amount):
        return self.balance >= amount