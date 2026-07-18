# gov_integration/models/verification_request.py

from django.db import models
from django.conf import settings

def get_default_service_pk():
    from gov_integration.models.service_type import ServiceType
    from gov_integration.models.country_config import CountryConfig

    tanzania, _ = CountryConfig.objects.get_or_create(
        code="TZ",
        defaults={"name": "Tanzania"}
    )

    service, _ = ServiceType.objects.get_or_create(
        code="FREELANCER",
        defaults={
            "name": "Freelancer Service",
            "country": tanzania,
            "description": "Huduma kwa watu binafsi wanaojitegemea.",
            "is_active": True,
        }
    )
    return service.pk

class VerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    institution = models.ForeignKey('kiini.Institution', on_delete=models.SET_NULL, null=True, blank=True)
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_requests',
        help_text="Biashara husika, ikiwa ombi hili ni la uthibitisho wa biashara (mf. leseni)."
    )
    country = models.CharField(max_length=2)  # ISO2: TZ, KE, etc.
    service = models.ForeignKey(
        'gov_integration.ServiceType',  # string lazy reference to avoid import issues
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=get_default_service_pk,
        help_text="Service inayohusiana na ombi la uthibitishaji, default ni 'Freelancer Service'."
    )
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')    
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def verify(self):
        # simulate or do real request
        response = external_api_call(self.payload)
        self.response_data = response
        self.status = "VERIFIED" if response.get("verified") else "FAILED"
        self.save()
        return self.status == "VERIFIED"