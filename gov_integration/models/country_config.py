# gov_integration/models/country_config.py
from django.db import models

class CountryConfig(models.Model):
    ISO_CODES = [
        ('TZ', 'Tanzania'),
        ('KE', 'Kenya'),
        ('UG', 'Uganda'),
        ('RW', 'Rwanda'),
        ('BI', 'Burundi'),
        ('SS', 'South Sudan'),
    ]

    code = models.CharField(max_length=2, choices=ISO_CODES, unique=True)
    name = models.CharField(max_length=50)
    currency = models.CharField(max_length=10, default='TZS')
    integration_ready = models.BooleanField(default=False)
    default_language = models.CharField(max_length=20, default='en')
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name
        
