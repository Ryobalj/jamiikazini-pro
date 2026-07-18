from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import F
from businesses.models.order import Order, OrderItem, OrderStatus
from businesses.models.product import Product
from businesses.models.booking import Booking
from businesses.models.booking import Booking, BookingLog
from businesses.models.featured_listing import FeaturedListing
from payments.models.invoice import Invoice, InvoiceStatus


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Recalculate total_amount when order items change."""
    order = instance.order
    order.save()


@receiver(post_save, sender=OrderItem)
def decrement_stock_on_order_item_created(sender, instance, created, **kwargs):
    """
    Punguza quantity_in_stock ya bidhaa order item MPYA inapoundwa. Haifanyiki
    kwa updates za baadaye (created=False) ili isipunguze mara mbili. F()
    inatumika kuepuka race condition ya read-modify-write.
    """
    if not created or not instance.product_id:
        return
    Product.objects.filter(pk=instance.product_id).update(
        quantity_in_stock=F("quantity_in_stock") - instance.quantity
    )


@receiver(pre_save, sender=Order)
def capture_previous_order_status(sender, instance, **kwargs):
    """Hifadhi status ya awali (kabla ya save) kwenye instance ili post_save iweze
    kutambua kama hii ni MABADILIKO kuelekea CANCELLED/REFUNDED, si re-save tu."""
    if instance.pk:
        instance._previous_status = (
            Order.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        )
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def restore_stock_on_cancel_or_refund(sender, instance, created, **kwargs):
    """
    Rejesha (ongeza) quantity_in_stock ya bidhaa endapo order IMEBADILIKA kuwa
    CANCELLED au REFUNDED (si order mpya, na si re-save ya order iliyokwisha
    kuwa kwenye hali hiyo - hivyo haitarejesha mara mbili).
    """
    if created:
        return
    restock_statuses = {OrderStatus.CANCELLED, OrderStatus.REFUNDED}
    previous_status = getattr(instance, "_previous_status", None)
    if instance.status in restock_statuses and previous_status not in restock_statuses:
        for item in instance.items.filter(product__isnull=False):
            Product.objects.filter(pk=item.product_id).update(
                quantity_in_stock=F("quantity_in_stock") + item.quantity
            )


@receiver(post_save, sender=Invoice)
def activate_featured_listing_on_invoice_paid(sender, instance, **kwargs):
    """Fanya FeaturedListing kuwa hai (is_active=True) mara tu invoice yake ikilipwa."""
    if instance.status == InvoiceStatus.PAID:
        FeaturedListing.objects.filter(invoice=instance, is_active=False).update(is_active=True)

