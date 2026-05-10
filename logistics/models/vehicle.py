# logistics/models/vehicle.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from logistics.choices import TransportTypeChoices
from logistics.models import TransportProvider, Driver
from logistics.constants.vehicle_types import VehicleType


class VerificationStatus(models.TextChoices):
    VERIFIED = "verified", _("Verified")
    PENDING = "pending", _("Pending")
    FAILED = "failed", _("Failed")


class Vehicle(models.Model):
    provider = models.ForeignKey(
        TransportProvider,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )

    vehicle_type = models.CharField(
        max_length=30,
        choices=TransportTypeChoices.choices,
        verbose_name=_("Vehicle Type")
    )

    registration_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Registration Number")
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Model Name")
    )

    capacity_kg = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Maximum weight capacity in kilograms"),
        verbose_name=_("Weight Capacity (kg)")
    )

    volume_cbm = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Maximum volume capacity in cubic meters"),
        verbose_name=_("Volume Capacity (m³)")
    )

    image = models.ImageField(
        upload_to='vehicles/images/',
        null=True,
        blank=True,
        verbose_name=_("Vehicle Image")
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    # Drivers
    drivers = models.ManyToManyField(
        Driver,
        related_name='vehicles',
        blank=True,
        verbose_name=_("Assigned Drivers")
    )

    active_driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_vehicles',
        verbose_name=_("Active Driver")
    )

    verification_statuses = models.JSONField(
        default=dict,
        help_text=_("""
            Example:
            {
                "TRA": "verified",
                "LATRA": "pending",
                "POLICE": "verified",
                "INSURANCE": "failed"
            }
        """),
        verbose_name=_("Verification Statuses")
    )

    notes = models.TextField(blank=True, null=True, verbose_name=_("Internal Notes"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def clean(self):
        if self.pk and self.drivers.count() > 2:
            raise ValidationError(_("A maximum of 2 drivers can be assigned to a vehicle."))
        if self.active_driver and self.active_driver not in self.drivers.all():
            raise ValidationError(_("Active driver must be one of the assigned drivers."))

    @property
    def is_fully_verified(self):
        return all(status == VerificationStatus.VERIFIED for status in self.verification_statuses.values())

    def __str__(self):
        return f"{self.registration_number} - {self.get_vehicle_type_display()}"