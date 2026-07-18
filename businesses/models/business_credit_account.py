# businesses/models/business_credit_account.py

from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business


class BusinessCreditAccount(UUIDModel, TimeStampedModel):
    """
    Kikomo cha mkopo (credit limit) kwa biashara inayonunua kwa masharti ya
    NET_15/NET_30 badala ya kulipa mara moja. Default ni sifuri - hakuna
    mkopo mpaka umeidhinishwa wazi (default salama). outstanding_credit
    huongezeka order ya mkopo inapoundwa, na hupungua invoice inapolipwa.
    """
    business = models.OneToOneField(
        Business, on_delete=models.CASCADE, related_name="credit_account",
        verbose_name=_("Business"),
    )
    credit_limit = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        verbose_name=_("Credit Limit"),
    )
    outstanding_credit = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        verbose_name=_("Outstanding Credit"),
    )

    class Meta:
        verbose_name = _("Business Credit Account")
        verbose_name_plural = _("Business Credit Accounts")

    def __str__(self):
        return f"{self.business.name}: {self.outstanding_credit}/{self.credit_limit}"

    @property
    def available_credit(self):
        return self.credit_limit - self.outstanding_credit
