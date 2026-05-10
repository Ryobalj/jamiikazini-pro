# kiini/models/department.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import UUIDModel, TimeStampedModel
from .institution import Institution

class Department(UUIDModel, TimeStampedModel):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name=_("Institution")
    )
    name = models.CharField(max_length=255, verbose_name=_("Department Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        unique_together = ("institution", "name")  # ensures uniqueness per institution
        ordering = ("institution__name", "name")

    def __str__(self):
        return f"{self.name} ({self.institution.name})"