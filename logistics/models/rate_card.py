# logistics/models/rate_card.py

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from logistics.choices import TransportTypeChoices


class TransportRateCard(models.Model):
    """
    Kiwango cha bei kwa kila aina ya usafiri - kinatumika kukadiria (estimate)
    gharama ya usafirishaji kabla dereva hajakubali kazi. Kinaweza kubadilishwa
    na admin bila kuhitaji deploy mpya.
    """
    vehicle_type = models.CharField(
        max_length=30,
        choices=TransportTypeChoices.choices,
        unique=True,
        verbose_name=_("Vehicle Type"),
    )
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Base Fare"))
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Rate per Km"))
    minimum_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Minimum Fare"))
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Transport Rate Card")
        verbose_name_plural = _("Transport Rate Cards")

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - base {self.base_fare} + {self.per_km_rate}/km"

    def estimate_fare(self, distance_km):
        estimated = self.base_fare + (self.per_km_rate * Decimal(str(distance_km)))
        return max(estimated, self.minimum_fare)
