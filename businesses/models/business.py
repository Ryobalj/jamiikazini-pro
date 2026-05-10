# businesses/models/business.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from kiini.models.base_entity import AbstractEntity
from kiini.models.institution import Institution
from businesses.models.category import BusinessCategory
from accounts.models import User

class Business(AbstractEntity):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='businesses',
        verbose_name=_("Institution"),
        help_text=_("Taasisi inayosimamia biashara hii.")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Maelezo mafupi kuhusu biashara.")
    )

    category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="businesses",
        verbose_name=_("Business Category"),
        help_text=_("Aina au sekta ya biashara.")
    )

    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
        help_text=_("Tovuti rasmi ya biashara (kama ipo).")
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Is Verified"),
        help_text=_("Je biashara hii imethibitishwa rasmi?")
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly version of the business name.")
    )

    class Meta:
        verbose_name = _("Business")
        verbose_name_plural = _("Businesses")
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def website_url(self):
        if self.institution and self.institution.domain:
            return f"{slugify(self.name)}.{self.institution.domain}"
        return ""

    def __str__(self):
        return self.name