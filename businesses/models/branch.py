# businesses/models/branch.py

from django.db import models
from django.contrib.gis.db.models import PointField
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from businesses.models.service import Service

class Branch(UUIDModel, TimeStampedModel):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name=_("Business"),
        help_text=_("Biashara inayomiliki tawi hili.")
    )

    services = models.ManyToManyField(
        Service,
        related_name="branches",
        blank=True,
        verbose_name=_("Services at Branch"),
        help_text=_("Huduma zinazotolewa katika tawi hili.")
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Branch Name"),
        help_text=_("Jina la tawi la biashara.")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Maelezo mafupi kuhusu tawi hili.")
    )

    location = PointField(
        geography=True,
        null=True,
        blank=True,
        verbose_name=_("Location"),
        help_text=_("Mahali ambapo tawi hili linapatikana (latitude/longitude).")
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("Phone"),
        help_text=_("Nambari ya simu ya mawasiliano ya tawi.")
    )

    email = models.EmailField(
        blank=True,
        verbose_name=_("Email"),
        help_text=_("Barua pepe ya tawi (si lazima).")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Je, tawi hili linafanya kazi kwa sasa?")
    )

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.business.name}"