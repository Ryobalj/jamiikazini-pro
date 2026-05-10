# logistics/models/location.py

from django.db import models
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Location Name"))
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Address"))
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name=_("Latitude")
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name=_("Longitude")
    )
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
   
    def update_from_gps(self, latitude, longitude):
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Invalid latitude or longitude values.")
            self.latitude = latitude
            self.longitude = longitude
            self.save(update_fields=["latitude", "longitude"])

    def __str__(self):
        return self.name
