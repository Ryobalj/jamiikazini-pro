# businesses/models/order.py

from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel
from accounts.models import User
from businesses.models.business import Business
from businesses.models.product import Product
from businesses.models.service import Service


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    REFUNDED = "REFUNDED", _("Refunded")


class PaymentStatus(models.TextChoices):
    UNPAID = "UNPAID", _("Unpaid")
    PAID = "PAID", _("Paid")
    FAILED = "FAILED", _("Failed")
    REFUNDED = "REFUNDED", _("Refunded")


class Order(UUIDModel, TimeStampedModel):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Client"),
        help_text=_("User who placed the order"),
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Business"),
        help_text=_("Business that received the order"),
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        verbose_name=_("Order Status"),
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name=_("Payment Status"),
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Amount"),
        help_text=_("Sum of all order items."),
    )
    notes = models.TextField(blank=True, verbose_name=_("Order Notes"))
    scheduled_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled Date & Time"),
        help_text=_("For scheduled services or deliveries."),
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]

    def __str__(self):
        """String representation for Order."""
        return f"Order {self.id} by {self.client.email} - Status: {self.status}"

    def calculate_total(self) -> Decimal:
        """Calculate total from order items."""
        return sum(item.total_price for item in self.items.all())

    def save(self, *args, **kwargs):
        """Override save to always ensure total_amount is calculated."""
        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)


class OrderItem(UUIDModel, TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Order"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name=_("Product"),
        null=True,
        blank=True,
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name=_("Service"),
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Unit Price"),
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Price"),
    )

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        constraints = [
            models.CheckConstraint(
                check=models.Q(product__isnull=False) | models.Q(service__isnull=False),
                name="order_item_product_or_service_not_null"
            )
        ]

    def save(self, *args, **kwargs):
        """Automatically set total_price and update parent order total_amount."""
        self.total_price = self.get_total_price()
        super().save(*args, **kwargs)

        # Baada ya OrderItem kuhifadhiwa, weka total_amount ya parent order
        self.order.total_amount = self.order.calculate_total()
        self.order.save(update_fields=["total_amount"])

    def get_total_price(self) -> Decimal:
        """Calculate total price for this item."""
        return self.unit_price * self.quantity

    def __str__(self) -> str:
        """Return readable name for OrderItem."""
        item_name = self.product.name if self.product else (self.service.name if self.service else "Unknown Item")
        return f"{self.quantity} x {item_name}"