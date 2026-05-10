from django.db.models.signals import post_save
from django.dispatch import receiver
from logistics.models.transport_assignment import TransportAssignment
from kiini.helpers.notification_helper import notify_user


@receiver(post_save, sender=TransportAssignment)
def send_assignment_notification(sender, instance, created, **kwargs):
    if created:
        notify_user(instance.request.created_by, f"Request assigned to {instance.vehicle}")
    elif instance.status == 'IN_TRANSIT':
        notify_user(instance.request.created_by, f"Your delivery is in transit.")
    elif instance.status == 'COMPLETED':
        notify_user(instance.request.created_by, f"Your delivery has been completed.")
    elif instance.status == 'CANCELLED':
        notify_user(instance.request.created_by, f"Your delivery has been cancelled.")

