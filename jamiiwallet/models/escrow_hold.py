# jamiiwallet/models/escrow_hold.py

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet


class EscrowHoldStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    CLOSED = "CLOSED", _("Closed")


class EscrowHold(UUIDModel, TimeStampedModel):
    """
    Ledger ya itemized juu ya HOLD moja ya Transaction - Wallet.held_balance ni
    counter ya jumla tu (haitofautishi HOLD gani inayolipwa kwa CAPTURE gani).
    EscrowHold inafuatilia kiasi gani cha HOLD maalum tayari kime-CAPTURE-iwa au
    kime-VOID-iwa, ili miradi/mikataba yenye malipo ya awamu (ujenzi, kilimo)
    isiweze kutoa zaidi ya ilivyoshikiliwa - bila kugusa TransactionEngine wala
    escrow ya delivery iliyopo (logistics/services/escrow_release.py), ambayo
    inaendelea kuita TransactionEngine moja kwa moja bila kujua EscrowHold hii.
    """
    hold_transaction = models.OneToOneField(
        Transaction, on_delete=models.PROTECT, related_name="escrow_hold",
    )
    wallet = models.ForeignKey(
        Wallet, on_delete=models.PROTECT, related_name="escrow_holds",
    )
    total_held = models.DecimalField(max_digits=18, decimal_places=2)
    total_captured = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_voided = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(
        max_length=10, choices=EscrowHoldStatus.choices, default=EscrowHoldStatus.OPEN,
    )

    # Generic link kwa chochote kinachotumia hold hii (ConstructionProject,
    # HarvestContract, PropertyListing, n.k.) - UUIDField kwenye modeli hizo
    # zote, hivyo object_id inahifadhiwa kama string.
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL,
    )
    object_id = models.CharField(max_length=64, null=True, blank=True)
    linked_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Escrow Hold")
        verbose_name_plural = _("Escrow Holds")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["wallet", "status"]),
        ]

    def __str__(self):
        return f"EscrowHold({self.total_held}, remaining={self.remaining}, {self.status})"

    @property
    def remaining(self):
        return self.total_held - self.total_captured - self.total_voided
