# kiini/models/institution_type.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import TimeStampedModel, UUIDModel

class InstitutionType(UUIDModel, TimeStampedModel):
    class TypeChoices(models.TextChoices):
        PRIMARY_SCHOOL = 'PRIMARY_SCHOOL', _("Primary School")
        SECONDARY_SCHOOL = 'SECONDARY_SCHOOL', _("Secondary School")
        COLLEGE = 'COLLEGE', _("College")
        UNIVERSITY = 'UNIVERSITY', _("University")
        VTC = 'VTC', _("Vocational Training Center")
        HOSPITAL = 'HOSPITAL', _("Hospital")
        HEALTH_CENTER = 'HEALTH_CENTER', _("Health Center")
        DISPENSARY = 'DISPENSARY', _("Dispensary")
        CLINIC = 'CLINIC', _("Clinic")
        NGO = 'NGO', _("Non-Governmental Organization")
        CBO = 'CBO', _("Community-Based Organization")
        FBO = 'FBO', _("Faith-Based Organization")
        PRIVATE_COMPANY = 'PRIVATE_COMPANY', _("Private Company")
        PUBLIC_CORPORATION = 'PUBLIC_CORPORATION', _("Public Corporation")
        COOPERATIVE = 'COOPERATIVE', _("Cooperative Society")
        GOVERNMENT_MINISTRY = 'GOVERNMENT_MINISTRY', _("Government Ministry")
        MUNICIPAL_COUNCIL = 'MUNICIPAL_COUNCIL', _("Municipal Council")
        PARASTATAL = 'PARASTATAL', _("Parastatal Organization")
        RELIGIOUS_INSTITUTION = 'RELIGIOUS_INSTITUTION', _("Religious Institution")
        TRAINING_INSTITUTE = 'TRAINING_INSTITUTE', _("Training Institute")

    name = models.CharField(
        max_length=50,
        choices=TypeChoices.choices,
        unique=True,
        verbose_name=_("Type Name")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta:
        verbose_name = _("Institution Type")
        verbose_name_plural = _("Institution Types")

    def __str__(self):
        return self.get_name_display()