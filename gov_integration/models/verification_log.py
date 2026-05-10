# gov_integration/models/verification_log.py
from django.db import models
from .verification_request import VerificationRequest

class VerificationLog(models.Model):
    request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    raw_response = models.TextField(blank=True)