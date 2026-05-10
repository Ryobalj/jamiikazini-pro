from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from businesses.models.order import OrderItem
from businesses.models.booking import Booking
from businesses.models.booking import Booking, BookingLog


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Recalculate total_amount when order items change."""
    order = instance.order
    order.save()
    
