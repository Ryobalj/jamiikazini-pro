# businesses/models/service.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from kiini.models.base import UUIDModel, TimeStampedModel


class BillingType(models.TextChoices):
    ONE_TIME = "ONE_TIME", _("One-time")
    HOURLY = "HOURLY", _("Per Hour")
    DAILY = "DAILY", _("Per Day")
    WEEKLY = "WEEKLY", _("Per Week")
    MONTHLY = "MONTHLY", _("Per Month")


class ServiceLocationType(models.TextChoices):
    PROVIDER_LOCATION = "PROVIDER", _("At Provider Location")
    CLIENT_LOCATION = "CLIENT", _("At Client Location")
    REMOTE = "REMOTE", _("Remote / Online")


class Service(UUIDModel, TimeStampedModel):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("Business"),
        help_text=_("Biashara inayotoa huduma hii.")
    )

    category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Category"),
        help_text=_("Aina ya huduma au biashara inayohusiana.")
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Service Name"),
        help_text=_("Jina la huduma.")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Maelezo ya huduma.")
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Price"),
        help_text=_("Gharama ya huduma.")
    )

    billing_type = models.CharField(
        max_length=20,
        choices=BillingType.choices,
        default=BillingType.ONE_TIME,
        verbose_name=_("Billing Type"),
        help_text=_("Jinsi malipo yanavyofanyika: kwa mara moja, kwa saa, au muda mwingine.")
    )

    location_type = models.CharField(
        max_length=20,
        choices=ServiceLocationType.choices,
        default=ServiceLocationType.PROVIDER_LOCATION,
        verbose_name=_("Service Location Type"),
        help_text=_("Mahali pa kutolea huduma: kwa mtoa huduma, kwa mteja, au mtandaoni.")
    )

    requires_booking = models.BooleanField(
        default=False,
        verbose_name=_("Requires Booking"),
        help_text=_("Inaonesha kama huduma inahitaji kuweka miadi (booking).")
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name=_("Is Available"),
        help_text=_("Huduma inapatikana kwa sasa.")
    )

    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Duration (Minutes)"),
        help_text=_("Muda wa makadirio kwa huduma hii kwa dakika.")
    )

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")

    def __str__(self):
        return f"{self.name} - {self.business.name}"