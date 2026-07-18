# logistics/models/transport_assignment.py

from django.db import models
from django.contrib.gis.db.models import PointField
from django.utils import timezone
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle

class TransportAssignment(models.Model):
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_IN_TRANSIT = 'IN_TRANSIT'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    VALID_TRANSITIONS = {
        STATUS_ASSIGNED: [STATUS_IN_TRANSIT, STATUS_CANCELLED],
        STATUS_IN_TRANSIT: [STATUS_DELIVERED, STATUS_CANCELLED],
        STATUS_DELIVERED: [STATUS_COMPLETED],
    }

    transport_request = models.OneToOneField(TransportRequest, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(TransportProvider, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    assignment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ASSIGNED
    )
    pickup_time = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    current_location = PointField(geography=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    agreed_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    client_confirmed_at = models.DateTimeField(null=True, blank=True)

    def update_status(self, new_status):
        if new_status == self.assignment_status:
            return  # No change

        allowed = self.VALID_TRANSITIONS.get(self.assignment_status, [])
        if new_status not in allowed:
            raise ValueError(f"Cannot change status from {self.assignment_status} to {new_status}")

        self.assignment_status = new_status
        self.save()

        from kiini.helpers.notification_helper import notify_user
        notify_user(self.assigned_to.user, f"Assignment status changed to {new_status.replace('_', ' ').title()}.")

        if new_status == self.STATUS_DELIVERED:
            from logistics.services.escrow_release import release_escrow_if_ready
            release_escrow_if_ready(self)

    # Optional wrappers
    def mark_in_transit(self):
        self.update_status(self.STATUS_IN_TRANSIT)

    def mark_delivered(self):
        self.update_status(self.STATUS_DELIVERED)

    def mark_completed(self):
        self.update_status(self.STATUS_COMPLETED)

    def cancel_assignment(self):
        self.update_status(self.STATUS_CANCELLED)

    def confirm_receipt(self):
        """Mnunuzi anathibitisha amepokea bidhaa - hii ni sharti mojawapo la kuachilia fedha za escrow."""
        if self.assignment_status != self.STATUS_DELIVERED:
            raise ValueError("Order haijaonyeshwa kama imefikishwa bado.")
        self.client_confirmed_at = timezone.now()
        self.save(update_fields=["client_confirmed_at"])
        from logistics.services.escrow_release import release_escrow_if_ready
        release_escrow_if_ready(self)

    def __str__(self):
        return f"Assignment for {self.transport_request.id} to {self.assigned_to}"