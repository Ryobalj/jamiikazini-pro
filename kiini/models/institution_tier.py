# kiini/models/institution_tier.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import UUIDModel, TimeStampedModel


class InstitutionTier(UUIDModel, TimeStampedModel):
    class TierChoices(models.TextChoices):
        MICRO = 'MICRO', _("Micro Enterprise")
        SMALL = 'SMALL', _("Small Enterprise")
        MEDIUM = 'MEDIUM', _("Medium Enterprise")
        LARGE = 'LARGE', _("Large Enterprise")
        ENTERPRISE = 'ENTERPRISE', _("Corporate / Enterprise")

    name = models.CharField(
        max_length=20,
        choices=TierChoices.choices,
        unique=True,
        verbose_name=_("Tier Name")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta:
        verbose_name = _("Institution Tier")
        verbose_name_plural = _("Institution Tiers")
        ordering = ["name"]

    def __str__(self):
        return self.get_name_display()