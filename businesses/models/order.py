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
    HELD = "HELD", _("Held")
    PAID = "PAID", _("Paid")
    FAILED = "FAILED", _("Failed")
    REFUNDED = "REFUNDED", _("Refunded")
    CASH_PENDING = "CASH_PENDING", _("Cash Pending")


class FulfillmentType(models.TextChoices):
    PICKUP = "PICKUP", _("Pickup")
    DELIVERY = "DELIVERY", _("Delivery")


class PaymentMethod(models.TextChoices):
    WALLET = "WALLET", _("JamiiWallet")
    CASH = "CASH", _("Cash")


class PaymentTerms(models.TextChoices):
    IMMEDIATE = "IMMEDIATE", _("Immediate")
    NET_15 = "NET_15", _("Net 15")
    NET_30 = "NET_30", _("Net 30")


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
    purchasing_business = models.ForeignKey(
        Business,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchases",
        verbose_name=_("Purchasing Business"),
        help_text=_("Biashara inayonunua (B2B) - imewekwa tu client anaponunua "
                     "'kama biashara yake', si mtu binafsi. Null = ununuzi wa "
                     "kawaida wa rejareja, tabia haibadiliki kabisa."),
    )
    payment_terms = models.CharField(
        max_length=20,
        choices=PaymentTerms.choices,
        default=PaymentTerms.IMMEDIATE,
        verbose_name=_("Payment Terms"),
        help_text=_("NET_15/NET_30 zinapatikana tu kwa purchasing_business yenye "
                     "mkopo (BusinessCreditAccount) - vinginevyo IMMEDIATE pekee."),
    )
    invoice = models.OneToOneField(
        "payments.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="b2b_order",
        verbose_name=_("Invoice"),
        help_text=_("Invoice ya malipo ya mkopo - imewekwa tu kama payment_terms != IMMEDIATE."),
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
    fulfillment_type = models.CharField(
        max_length=20,
        choices=FulfillmentType.choices,
        default=FulfillmentType.PICKUP,
        verbose_name=_("Fulfillment Type"),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.WALLET,
        verbose_name=_("Payment Method"),
        help_text=_("CASH inaruhusiwa tu kwa PICKUP na biashara iliyothibitishwa (is_verified) - "
                    "fedha hazishikiliwi (escrow), mnunuzi analipa taslimu akichukua bidhaa."),
    )
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referred_orders",
        verbose_name=_("Referred By"),
        help_text=_("Dalali aliyeleta mnunuzi kwenye oda hii (kwa msimbo wa rufaa) - "
                    "null = ununuzi wa kawaida bila dalali, tabia haibadiliki kabisa."),
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Delivery Fee"),
        help_text=_("Bei ya usafiri, inajumuishwa kwenye total_amount kama fulfillment_type ni DELIVERY."),
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]

    def __str__(self):
        """String representation for Order."""
        return f"Order {self.id} by {self.client.email} - Status: {self.status}"

    def calculate_total(self) -> Decimal:
        """Calculate total from order items plus any delivery fee."""
        items_total = sum(item.total_price for item in self.items.all())
        return items_total + self.delivery_fee

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
    quantity = models.DecimalField(
        max_digits=10, decimal_places=3, default=Decimal("1.000"), verbose_name=_("Quantity")
    )
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