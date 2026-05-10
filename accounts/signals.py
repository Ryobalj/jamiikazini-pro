from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_delete, pre_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from .models import LoginHistory
from jamiiwallet.models.wallet import Wallet
from kiini.models import Institution

User = get_user_model()

# ------------------- LOGIN SIGNALS ------------------- #

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    LoginHistory.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        was_successful=True
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request=None, **kwargs):
    try:
        user = User.objects.get(email=credentials.get('email'))
    except (User.DoesNotExist, TypeError, ValueError):
        user = None

    ip_address = get_client_ip(request) if request else ''
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

    if user:
        LoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            was_successful=False
        )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


# ------------------- USER CLEANUP SIGNALS ------------------- #

@receiver(post_delete, sender=User)
def deactivate_wallet_on_user_delete(sender, instance, **kwargs):
    Wallet.objects.filter(user=instance).update(is_active=False)


@receiver(pre_save, sender=User)
def deactivate_wallet_on_user_deactivation(sender, instance, **kwargs):
    if not instance.pk:
        return  # new user being created

    try:
        old_user = User.objects.get(pk=instance.pk)
        if old_user.is_active and not instance.is_active:
            Wallet.objects.filter(user=instance).update(is_active=False)
    except User.DoesNotExist:
        pass


# ------------------- DEFAULT INSTITUTION SETUP ------------------- #

@receiver(post_migrate)
def create_default_institution(sender, **kwargs):
    # Hii itahakikisha tunakuwa na institution ya "Jamiikazini User" baada ya migrations zote
    Institution.objects.get_or_create(name="Jamiikazini User")