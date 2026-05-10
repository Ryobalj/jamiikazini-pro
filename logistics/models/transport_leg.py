# logistics/models/transport_leg.py

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from logistics.models import TransportProvider, Shipment


class TransportMode(models.TextChoices):
    TRUCK = "TRUCK", _("Truck")
    DRONE = "DRONE", _("Drone")
    BOAT = "BOAT", _("Boat")
    TRAIN = "TRAIN", _("Train")
    BIKE = "BIKE", _("Bike")
    AIR = "AIR", _("Airplane")
    OTHER = "OTHER", _("Other")


class LegStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", _("Scheduled")
    DISPATCHED = "DISPATCHED", _("Dispatched")
    IN_TRANSIT = "IN_TRANSIT", _("In Transit")
    DELAYED = "DELAYED", _("Delayed")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    FAILED = "FAILED", _("Failed")


class TransportLeg(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="legs")
    provider = models.ForeignKey(TransportProvider, on_delete=models.SET_NULL, null=True, related_name="legs")

    sequence_number = models.PositiveIntegerField(help_text=_("Order of leg in shipment route"))

    origin_name = models.CharField(max_length=255)
    origin_coords = gis_models.PointField(geography=True)

    destination_name = models.CharField(max_length=255)
    destination_coords = gis_models.PointField(geography=True)

    mode = models.CharField(max_length=20, choices=TransportMode.choices)
    status = models.CharField(max_length=20, choices=LegStatus.choices, default=LegStatus.SCHEDULED)

    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)

    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    current_location = gis_models.PointField(geography=True, null=True, blank=True)
    last_tracked_at = models.DateTimeField(null=True, blank=True)

    # Cost breakdown
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    distance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    jamiikazini_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, help_text=_("Total cost for this leg"))

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["shipment", "sequence_number"]
        unique_together = ("shipment", "sequence_number")

    def __str__(self):
        return f"Leg #{self.sequence_number} - {self.origin_name} to {self.destination_name}"


class LegStatusLog(models.Model):
    leg = models.ForeignKey(TransportLeg, on_delete=models.CASCADE, related_name="status_logs")
    status = models.CharField(max_length=20, choices=LegStatus.choices)
    remarks = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leg} - {self.status} @ {self.timestamp}"