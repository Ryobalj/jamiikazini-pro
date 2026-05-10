# logistics/signals/transport_verification_signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
import logging

from gov_integration.models.verification_request import VerificationRequest
from logistics.models.transport_provider_verification import TransportProviderVerification

logger = logging.getLogger(__name__)

@receiver(post_save, sender=VerificationRequest)
def update_transport_provider_status(sender, instance, **kwargs):
    """
    Automatically update the overall status of TransportProviderVerification
    when a related VerificationRequest is updated.
    """
    try:
        verification = TransportProviderVerification.objects.get(
            Q(nida_verification=instance) |
            Q(driving_license_verification=instance) |
            Q(vehicle_license_verification=instance) |
            Q(latra_permit_verification=instance)
        )
        verification.update_overall_status()
        logger.info(f"Transport verification status updated for user {verification.user_id}")
    except TransportProviderVerification.DoesNotExist:
        logger.debug("No TransportProviderVerification linked to this VerificationRequest.")