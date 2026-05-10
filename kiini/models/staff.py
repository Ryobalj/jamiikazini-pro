# kiini/models/staff.py

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .base import UUIDModel, TimeStampedModel
from .institution import Institution
from .department import Department

class StaffProfile(UUIDModel, TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="staff_profiles",
        verbose_name=_("Institution")
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profiles",
        verbose_name=_("Department")
    )
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Title"))
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Position"))
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Phone Number"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("Staff Profile")
        verbose_name_plural = _("Staff Profiles")
        unique_together = ("user", "institution")
        ordering = ("institution", "user")  # sahihi

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.institution.name}"