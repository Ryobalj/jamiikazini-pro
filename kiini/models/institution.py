# kiini/models/institution.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from .institution_tier import InstitutionTier
from .institution_type import InstitutionType
from .base_entity import AbstractEntity

class Institution(AbstractEntity):
    # null (not "") when the institution has no domain yet: unique=True allows
    # many NULLs but only ONE empty string - a second domainless institution
    # would otherwise crash with IntegrityError.
    domain = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Subdomain"),
        help_text=_(
            "Sehemu ya kwanza TU ya subdomain (mfano: 'shule-yangu'), SIO "
            "domain kamili - taasisi inapatikana kwenye "
            "https://<domain>.jamiikazini.com. Lazima ilingane na "
            "kile InstitutionMiddleware inachotafuta (parts[0] ya host)."
        )
    )

    def save(self, *args, **kwargs):
        if self.domain == "":
            self.domain = None
        super().save(*args, **kwargs)
    
    tier = models.ForeignKey(
        InstitutionTier,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Tier"),
        related_name="institutions"
    )

    institution_type = models.ForeignKey(
        InstitutionType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Institution Type"),
        related_name="institutions"
    )

    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("Metadata"),
        help_text=_("Taarifa za ziada kama config au settings.")
    )

    class Meta:
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")
        ordering = ['name']

    def __str__(self):
        return self.name