# savings/models/group_membership.py

from decimal import Decimal
from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from savings.models.savings_group import SavingsGroup


class GroupMemberRole(models.TextChoices):
    ADMIN = "ADMIN", _("Admin")
    MEMBER = "MEMBER", _("Member")


class GroupMembership(UUIDModel, TimeStampedModel):
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=10, choices=GroupMemberRole.choices, default=GroupMemberRole.MEMBER)
    # Kiasi kinachotarajiwa kila mzunguko - taarifa/kikumbusho tu, hakilazimishwi kikanuni.
    contribution_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Group Membership")
        verbose_name_plural = _("Group Memberships")
        unique_together = ("group", "user")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.email} @ {self.group.name} ({self.role})"
