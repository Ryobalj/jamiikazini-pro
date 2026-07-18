# kiini/models/referral_code.py

import secrets
import string
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel


def _generate_code():
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class ReferralCode(UUIDModel, TimeStampedModel):
    """
    Msimbo mfupi wa kila mtumiaji unaomruhusu kuwa "dalali" - anaposhirikisha
    msimbo huu na mnunuzi, na mnunuzi akauweka wakati wa checkout, oda
    inayotokana inapata Order.referred_by iliyowekwa, na dalali anapata
    kamisheni (angalia Business.broker_commission_rate na
    OrderSerializer._pay_broker_commission).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_code",
        verbose_name=_("User"),
    )
    code = models.CharField(max_length=12, unique=True, verbose_name=_("Referral Code"))

    class Meta:
        verbose_name = _("Referral Code")
        verbose_name_plural = _("Referral Codes")

    def save(self, *args, **kwargs):
        if not self.code:
            code = _generate_code()
            while ReferralCode.objects.filter(code=code).exists():
                code = _generate_code()
            self.code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.user.email})"

    @classmethod
    def get_or_create_for_user(cls, user):
        obj, _created = cls.objects.get_or_create(user=user)
        return obj
