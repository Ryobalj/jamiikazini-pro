# construction/models/project_milestone.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from construction.models.construction_project import ConstructionProject


class ProjectMilestoneStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    SUBMITTED = "SUBMITTED", _("Submitted")
    PAID = "PAID", _("Paid")


class ProjectMilestone(UUIDModel, TimeStampedModel):
    """
    Hatua moja ya mradi - jumla ya amount za milestones zote za mradi
    zinalingana kikamilifu na bei ya zabuni iliyoshinda (na hivyo na kiasi
    kilichoshikiliwa kwenye EscrowHold). Kuidhinishwa kwa mteja kunatoa
    (CAPTURE) kiasi cha hatua hiyo pekee kutoka kwenye HOLD moja - hatua
    nyingine zinabaki zimeshikiliwa mpaka nazo zikamilike.
    """
    project = models.ForeignKey(ConstructionProject, on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10, choices=ProjectMilestoneStatus.choices, default=ProjectMilestoneStatus.PENDING,
    )
    evidence_image = models.ImageField(upload_to="construction/milestones/", null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Project Milestone")
        verbose_name_plural = _("Project Milestones")
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Milestone({self.name}, {self.amount}, {self.status})"
