# logistics/models/vehicle_verification.py
#
# Uthibitisho wa GARI mahususi - tofauti na TransportProviderVerification
# (ambayo inathibitisha MTU: NIDA + leseni ya udereva, kitu kimoja tu kwa kila
# dereva). Gari moja lina usajili wake wa TRA na kibali chake cha LATRA
# mahususi, na mtoa-huduma (hasa kampuni) anaweza kuwa na magari mengi, kila
# moja likihitaji kuthibitishwa peke yake.

from django.db import models
from django.utils.translation import gettext_lazy as _
from gov_integration.models.verification_request import VerificationRequest


class VehicleVerification(models.Model):
    STATUS_CHOICES = (
        ('PENDING', _('Pending')),
        ('VERIFIED', _('Verified')),
        ('FAILED', _('Failed')),
    )

    vehicle = models.OneToOneField(
        'logistics.Vehicle', on_delete=models.CASCADE, related_name='verification'
    )
    tra_registration_verification = models.OneToOneField(
        VerificationRequest, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tra_vehicle_verification',
    )
    latra_permit_verification = models.OneToOneField(
        VerificationRequest, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='latra_vehicle_verification',
    )
    overall_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Vehicle Verification")
        verbose_name_plural = _("Vehicle Verifications")

    def __str__(self):
        return f"Verification for {self.vehicle.registration_number} - {self.get_overall_status_display()}"

    def update_overall_status(self):
        """
        TRA registration inahitajika kila wakati. Kibali cha LATRA kinahitajika
        tu kama gari lina latra_permit_number (si kila gari - baiskeli/boda
        binafsi hazihitaji kibali cha LATRA kama gari za kibiashara).
        """
        tra = self.tra_registration_verification
        latra_required = bool(self.vehicle.latra_permit_number)
        latra = self.latra_permit_verification

        if tra and tra.status == 'FAILED':
            self.overall_status = 'FAILED'
        elif latra_required and latra and latra.status == 'FAILED':
            self.overall_status = 'FAILED'
        elif tra and tra.status == 'VERIFIED' and (not latra_required or (latra and latra.status == 'VERIFIED')):
            self.overall_status = 'VERIFIED'
        else:
            self.overall_status = 'PENDING'

        self.save(update_fields=['overall_status', 'updated_at'])
