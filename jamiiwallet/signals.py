# jamiiwallet/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from jamiiwallet.models.wallet import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()


def get_default_currency():
    """Pata au unda default currency (TZS) kwa wallet mpya."""
    from payments.models.currency import Currency
    currency, _ = Currency.objects.get_or_create(
        code='TZS',
        defaults={
            'name': 'Tanzanian Shilling',
            'symbol': 'Tsh',
            'country': 'Tanzania',
            'is_active': True
        }
    )
    return currency


@receiver(post_save, sender=User)
def create_or_reactivate_wallet(sender, instance, created, **kwargs):
    if created:
        currency = get_default_currency()
        Wallet.objects.get_or_create(
            user=instance,
            defaults={'currency': currency}
        )
    else:
        wallet = Wallet.objects.filter(user=instance).first()
        if wallet and not wallet.is_active:
            wallet.is_active = True
            wallet.save()
        elif not wallet:
            currency = get_default_currency()
            Wallet.objects.create(user=instance, currency=currency)


@receiver(post_save, sender=Wallet)
def notify_balance_change(sender, instance, **kwargs):
    from jamiitasks.tasks.payment_tasks import notify_wallet_balance_change
    notify_wallet_balance_change.delay(
        wallet_id=instance.id,
        user_id=instance.user.id,
        new_balance=str(instance.balance)
    )