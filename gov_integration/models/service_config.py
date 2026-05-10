# gov_integration/models/service_config.py
from django.db import models
from .api_endpoint import ApiEndpoint

class ServiceConfig(models.Model):
    endpoint = models.ForeignKey(ApiEndpoint, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=512, blank=True)
    refresh_token = models.CharField(max_length=512, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.endpoint.name} Config"