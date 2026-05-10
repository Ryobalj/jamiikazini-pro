# gov_integration/models/service_type.py
from django.db import models
from .country_config import CountryConfig

class ServiceType(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)  # Iliyoongezwa
    country = models.ForeignKey(CountryConfig, on_delete=models.CASCADE, related_name='service_types')  # Iliyoongezwa
    is_active = models.BooleanField(default=True)  # Iliyoongezwa
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class CountryPolicy(models.Model):
    country = models.OneToOneField(CountryConfig, on_delete=models.CASCADE, related_name='policy')
    requires_mou = models.BooleanField(default=False)
    requires_license = models.BooleanField(default=False)
    local_partner_required = models.BooleanField(default=False)
    api_access_mode = models.CharField(max_length=50, default='private')  # public, private, pilot
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Policy for {self.country.name}"