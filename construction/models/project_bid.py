# construction/models/project_bid.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from construction.models.construction_project import ConstructionProject


class ProjectBidStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACCEPTED = "ACCEPTED", _("Accepted")
    REJECTED = "REJECTED", _("Rejected")


class ProjectBid(UUIDModel, TimeStampedModel):
    """Zabuni ya mkandarasi kwa mradi - tofauti na mifumo mingine ya
    broadcast+claim, hapa mteja HULINGANISHA zabuni kadhaa kabla ya kuchagua."""
    project = models.ForeignKey(ConstructionProject, on_delete=models.CASCADE, related_name="bids")
    contractor = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="project_bids")
    price = models.DecimalField(max_digits=14, decimal_places=2)
    timeline_days = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=ProjectBidStatus.choices, default=ProjectBidStatus.PENDING)

    class Meta:
        verbose_name = _("Project Bid")
        verbose_name_plural = _("Project Bids")
        ordering = ["price"]
        unique_together = ("project", "contractor")

    def __str__(self):
        return f"ProjectBid({self.contractor.name}, {self.price}, {self.status})"
