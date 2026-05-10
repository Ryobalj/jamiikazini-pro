# logistics/models/shipment.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from logistics.models import TransportProvider
from accounts.models import User  # Assuming Client is a type of User
from businesses.models.product import Product
from django.contrib.postgres.fields import ArrayField


class ShipmentStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    IN_TRANSIT = 'IN_TRANSIT', _('In Transit')
    DELIVERED = 'DELIVERED', _('Delivered')
    CANCELLED = 'CANCELLED', _('Cancelled')
    FAILED = 'FAILED', _('Failed')


class Shipment(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='shipments'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_shipments'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_shipments'
    )
    preferred_transport_modes = ArrayField(
        models.CharField(max_length=20),
        help_text="E.g. ['DRONE', 'BOAT', 'TRUCK']",
        default=list
    )
    route_details = models.JSONField(
        help_text="Suggested route path or waypoints if available",
        default=dict,
        blank=True
    )
    transport_providers = models.ManyToManyField(
        TransportProvider,
        related_name='shipments',
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PENDING
    )
    tax_paid = models.BooleanField(default=False)
    jamiikazini_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Final total paid by client")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_fully_paid(self):
        return self.tax_paid and self.transport_fee > 0

    def __str__(self):
        return f"Shipment #{self.id} from {self.sender} to {self.receiver}"