# savings/models/withdrawal_request.py

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from savings.models.savings_group import SavingsGroup
from jamiiwallet.models.transaction import Transaction


class WithdrawalRequestStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    EXECUTED = "EXECUTED", _("Executed")


class WithdrawalRequest(UUIDModel, TimeStampedModel):
    """
    Ombi la kutoa fedha kwenye GroupWallet - haliwezi kutekelezwa mpaka
    wanachama wa kutosha (kura, kulingana na SavingsGroup.approval_threshold_percent)
    waidhinishe. `required_approval_count` inahesabiwa wakati ombi
    linapoundwa (idadi ya wanachama wanaotumika wakati huo) ili kubadilika
    kwa uanachama baadaye kusiathiri ombi lililokwisha kuwa wazi.
    """
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="withdrawal_requests")
    requested_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_withdrawal_requests",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    purpose = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=WithdrawalRequestStatus.choices, default=WithdrawalRequestStatus.PENDING,
    )
    required_approval_count = models.PositiveIntegerField()
    destination_transaction = models.OneToOneField(
        Transaction, null=True, blank=True, on_delete=models.SET_NULL, related_name="group_withdrawal",
    )
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Withdrawal Request")
        verbose_name_plural = _("Withdrawal Requests")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"WithdrawalRequest({self.group.name}, {self.amount}, {self.status})"
