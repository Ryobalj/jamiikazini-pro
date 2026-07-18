# savings/models/group_wallet.py

from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from savings.models.savings_group import SavingsGroup
from payments.models.currency import Currency


class GroupWallet(UUIDModel, TimeStampedModel):
    """
    Mfuko wa pamoja wa kikundi - KWA MAKUSUDI si `jamiiwallet.Wallet` (ile ni
    ya mtu binafsi pekee, na TransactionEngine._transfer/_payment/_capture
    zote zinatafuta Wallet kwa `user_id`, hazina njia ya kutambua mmiliki wa
    aina nyingine). Badala ya kubadilisha Transaction (msingi unaotumiwa na
    kila awamu nyingine ya malipo), salio hili linadhibitiwa moja kwa moja na
    savings/services - fedha zinaingia kupitia WITHDRAWAL ya kawaida kutoka
    kwenye Wallet ya mwanachama, na kutoka kupitia TOP_UP ya kawaida kwenda
    kwenye Wallet ya mwanachama - Wallet/Transaction/TransactionEngine
    haziguswi kabisa.
    """
    group = models.OneToOneField(SavingsGroup, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="group_wallets")

    class Meta:
        verbose_name = _("Group Wallet")
        verbose_name_plural = _("Group Wallets")

    def __str__(self):
        return f"GroupWallet({self.group.name}, {self.balance})"
