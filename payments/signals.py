# payments/signals.py

import logging
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.db import connection
from django.utils.translation import gettext_lazy as _
from payments.models.payment_failure import PaymentFailure
from payments.models.currency import Currency
from jamiichat.utils import send_chat_message

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PaymentFailure)
def log_and_notify_payment_failure(sender, instance, created, **kwargs):
    if not created:
        return

    logger.error(
        f"[PAYMENT FAILURE] User={instance.user.id} | Ref={instance.reference} | "
        f"Amount={instance.amount} | Reason={instance.reason} | Retries={instance.retries}"
    )

    full_name = getattr(instance.user, "full_name", None) or _("Mteja")

    currency_obj = None
    if hasattr(instance, "currency") and instance.currency:
        currency_obj = Currency.objects.filter(code=instance.currency).first()

    currency_display = f"{currency_obj.symbol} " if currency_obj else _("Tsh. ")

    message = _(
        "Hujambo {full_name}, malipo yako ya {currency}{amount} kwa reference {ref} yameshindwa. "
        "Sababu: {reason}. Jaribu tena au wasiliana na huduma kwa wateja."
    ).format(
        full_name=full_name,
        currency=currency_display,
        amount=instance.amount,
        ref=instance.reference,
        reason=instance.reason,
    )

    try:
        send_chat_message(instance.user, message)
    except Exception as e:
        logger.error(f"Failed to send payment failure chat message to user {instance.user.id}: {e}")


# ---------- SAFE CURRENCY SEEDING ---------- #

def table_exists(table_name: str) -> bool:
    """Check if database table exists safely."""
    return table_name in connection.introspection.table_names()


@receiver(post_migrate)
def create_initial_currencies(sender, **kwargs):
    """Seed default currencies safely after migrating."""
    
    # Run only for payments app
    if sender.label != "payments":
        return

    # Ensure table exists (avoids migration crashes)
    if not table_exists("payments_currency"):
        logger.warning("payments_currency table not ready. Skipping seeding.")
        return

    try:
        from payments.models.currency import Currency
        from payments.seeds.currencies import seed_currencies

        seed_currencies(Currency)
        logger.info("Default currencies seeded successfully.")

    except Exception as exc:
        logger.error(f"Error while seeding currencies: {exc}")