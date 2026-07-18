# savings/models/savings_group.py

import secrets
import string
from decimal import Decimal
from django.conf import settings as django_settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from payments.models.currency import Currency


def _generate_invite_code():
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class SavingsGroup(UUIDModel, TimeStampedModel):
    """
    VICOBA/SACCOS - kikundi cha kuweka akiba pamoja. GroupWallet (mfuko wa
    pamoja) SI Wallet ya kawaida ya mtu binafsi - haifikiwi kwa Transfer au
    Withdrawal ya kawaida ya JamiiWallet; fedha zinaingia tu kupitia
    Contribution na kutoka tu kupitia WithdrawalRequest iliyokubaliwa na
    wanachama wa kutosha (kura, si mtu mmoja pekee).

    MUHIMU: Jamiikazini SI taasisi ya fedha yenye leseni - kikundi hiki ni
    zana ya kuwezesha makubaliano ya wanachama wenyewe, sio dhamana ya
    kibenki. Hii lazima ionekane wazi kwenye UI ya mfumo huu.
    """
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_groups_created",
    )
    invite_code = models.CharField(max_length=12, unique=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="savings_groups")

    # Asilimia ya wanachama wanaohitajika kuidhinisha ombi la kutoa fedha
    # kabla halijatekelezwa moja kwa moja - default 51 (wengi wa kawaida).
    approval_threshold_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("51.00"),
        validators=[MinValueValidator(Decimal("1.00")), MaxValueValidator(Decimal("100.00"))],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Savings Group")
        verbose_name_plural = _("Savings Groups")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.invite_code:
            code = _generate_invite_code()
            while SavingsGroup.objects.filter(invite_code=code).exists():
                code = _generate_invite_code()
            self.invite_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.invite_code})"
