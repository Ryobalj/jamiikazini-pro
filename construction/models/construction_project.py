# construction/models/construction_project.py

from django.conf import settings as django_settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from jamiiwallet.models.escrow_hold import EscrowHold


class ConstructionProjectStatus(models.TextChoices):
    OPEN = "OPEN", _("Open for Bids")
    AWARDED = "AWARDED", _("Awarded")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class ConstructionProject(UUIDModel, TimeStampedModel):
    """
    Mradi wa ujenzi/kandarasi - mteja anachapisha maelezo ya kazi, makandarasi
    wengi wanaweza kutoa zabuni (tofauti na ItemRequest/ImportRequest ambazo
    ni "wa kwanza kudai anashinda" - hapa mteja analinganisha zabuni kadhaa
    kabla ya kuchagua), kisha HOLD MOJA ya jumla ya bei ya zabuni iliyoshinda
    inashikiliwa mapema - kila hatua (milestone) inayokamilika na kukubaliwa
    na mteja inatoa sehemu yake kutoka kwenye HOLD hiyo hiyo.
    """
    client = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="construction_projects",
    )
    scope_description = models.TextField()
    location = gis_models.PointField(geography=True, null=True, blank=True)
    budget_ceiling = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    status = models.CharField(
        max_length=10, choices=ConstructionProjectStatus.choices, default=ConstructionProjectStatus.OPEN,
    )
    contractor = models.ForeignKey(
        Business, null=True, blank=True, on_delete=models.SET_NULL, related_name="construction_projects_as_contractor",
    )
    escrow_hold = models.ForeignKey(
        EscrowHold, null=True, blank=True, on_delete=models.SET_NULL, related_name="construction_project",
    )

    class Meta:
        verbose_name = _("Construction Project")
        verbose_name_plural = _("Construction Projects")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"ConstructionProject({self.scope_description[:40]}, {self.status})"
