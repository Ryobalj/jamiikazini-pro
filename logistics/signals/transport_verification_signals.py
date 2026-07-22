# logistics/signals/transport_verification_signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
import logging

from gov_integration.models.verification_request import VerificationRequest
from logistics.models.transport_provider_verification import TransportProviderVerification
from logistics.models.vehicle_verification import VehicleVerification

logger = logging.getLogger(__name__)

@receiver(post_save, sender=VerificationRequest)
def update_transport_provider_status(sender, instance, **kwargs):
    """
    Automatically update the overall status of TransportProviderVerification
    (person-level: NIDA + driver's license) when a related VerificationRequest
    is updated.
    """
    try:
        verification = TransportProviderVerification.objects.get(
            Q(nida_verification=instance) |
            Q(driving_license_verification=instance)
        )
        verification.update_overall_status()
        logger.info(f"Transport verification status updated for user {verification.user_id}")
    except TransportProviderVerification.DoesNotExist:
        logger.debug("No TransportProviderVerification linked to this VerificationRequest.")


@receiver(post_save, sender=VerificationRequest)
def update_vehicle_verification_status(sender, instance, **kwargs):
    """
    Automatically update the overall status of VehicleVerification
    (vehicle-level: TRA registration + LATRA permit) when a related
    VerificationRequest is updated.
    """
    try:
        verification = VehicleVerification.objects.get(
            Q(tra_registration_verification=instance) |
            Q(latra_permit_verification=instance)
        )
        verification.update_overall_status()
        logger.info(f"Vehicle verification status updated for vehicle {verification.vehicle_id}")
    except VehicleVerification.DoesNotExist:
        logger.debug("No VehicleVerification linked to this VerificationRequest.")
