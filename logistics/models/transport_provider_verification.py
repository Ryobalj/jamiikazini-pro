# logistics/models/transport_provider_verification.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from kiini.models.institution import Institution
from gov_integration.models.verification_request import VerificationRequest

class TransportProviderVerification(models.Model):
    PROVIDER_STATUS_CHOICES = (
        ('PENDING', _('Pending')),
        ('VERIFIED', _('Verified')),
        ('FAILED', _('Failed')),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transport_verification')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='transport_verifications')
    
    nida_verification = models.OneToOneField(VerificationRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='nida_transport_verification')
    driving_license_verification = models.OneToOneField(VerificationRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='driving_license_verification')
    vehicle_license_verification = models.OneToOneField(VerificationRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicle_license_verification')
    latra_permit_verification = models.OneToOneField(VerificationRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='latra_permit_verification')

    overall_status = models.CharField(max_length=20, choices=PROVIDER_STATUS_CHOICES, default='PENDING')

    # Fingerprint ya kudumu (HMAC-SHA256) ya namba ya leseni ya udereva
    # iliyothibitishwa - unique constraint inazuia dereva wawili tofauti
    # wasitumie leseni moja ya udereva. Sawa na User.national_id_hash.
    driver_license_hash = models.CharField(
        max_length=64, blank=True, null=True, unique=True, editable=False,
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Transport Provider Verification")
        verbose_name_plural = _("Transport Providers Verifications")

    def __str__(self):
        return f"Verification for {self.user.full_name} - {self.get_overall_status_display()}"

    def update_overall_status(self):
        """Automatically update the overall status based on individual verifications."""
        verifications = [
            self.nida_verification,
            self.driving_license_verification,
            self.vehicle_license_verification,
            self.latra_permit_verification,
        ]

        # Check if any verification failed
        if any(v and v.status == 'FAILED' for v in verifications):
            self.overall_status = 'FAILED'
        # Check if all verifications are verified
        elif all(v and v.status == 'VERIFIED' for v in verifications):
            self.overall_status = 'VERIFIED'
        # Otherwise, still pending
        else:
            self.overall_status = 'PENDING'

        self.save()