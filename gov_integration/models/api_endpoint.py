# gov_integration/models/api_endpoint.py
from django.db import models

class ApiEndpoint(models.Model):
    COUNTRY_CHOICES = [
        ('TZ', 'Tanzania'),
        ('KE', 'Kenya'),
        ('UG', 'Uganda'),
        ('RW', 'Rwanda'),
        ('BI', 'Burundi'),
        ('SS', 'South Sudan'),
    ]

    name = models.CharField(max_length=100)  # e.g. "NIDA Verification"
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    base_url = models.URLField()
    auth_type = models.CharField(max_length=30, default='JWT')  # JWT, OAuth2, API_KEY
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'gov_integration'

    def __str__(self):
        return f"{self.name} - {self.country}"
