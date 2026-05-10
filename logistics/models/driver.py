# logistics/models/driver.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel
from logistics.models import TransportProvider


class Driver(UUIDModel, TimeStampedModel):
    transport_provider = models.ForeignKey(
        TransportProvider, on_delete=models.CASCADE, related_name='drivers'
    )
    full_name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_image = models.ImageField(upload_to='drivers/profiles/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.full_name} ({self.license_number})"