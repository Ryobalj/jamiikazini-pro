# savings/models/withdrawal_approval.py

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from savings.models.withdrawal_request import WithdrawalRequest


class WithdrawalDecision(models.TextChoices):
    APPROVE = "APPROVE", _("Approve")
    REJECT = "REJECT", _("Reject")


class WithdrawalApproval(UUIDModel, TimeStampedModel):
    request = models.ForeignKey(WithdrawalRequest, on_delete=models.CASCADE, related_name="approvals")
    member = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_withdrawal_votes")
    decision = models.CharField(max_length=10, choices=WithdrawalDecision.choices)

    class Meta:
        verbose_name = _("Withdrawal Approval")
        verbose_name_plural = _("Withdrawal Approvals")
        unique_together = ("request", "member")

    def __str__(self):
        return f"Vote({self.member.email}, {self.decision})"
