# savings/models/contribution.py

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from savings.models.savings_group import SavingsGroup
from jamiiwallet.models.transaction import Transaction


class Contribution(UUIDModel, TimeStampedModel):
    """Mchango wa mwanachama kwenye GroupWallet - `source_transaction` ni
    WITHDRAWAL iliyotoa fedha kwenye Wallet ya kibinafsi ya mwanachama."""
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="contributions")
    member = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_contributions")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    source_transaction = models.OneToOneField(
        Transaction, null=True, blank=True, on_delete=models.SET_NULL, related_name="group_contribution",
    )

    class Meta:
        verbose_name = _("Contribution")
        verbose_name_plural = _("Contributions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Contribution({self.member.email}, {self.amount}, {self.group.name})"
