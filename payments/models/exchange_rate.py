# payments/models/exchange_rate.py 

from django.db import models
from kiini.models.base import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from payments.models.currency import Currency

class ExchangeRate(TimeStampedModel):
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="exchange_rates_base",
        verbose_name=_("Base Currency"),
        help_text=_("Sarafu ya msingi ambayo viwango vingine vinaendeshwa")
    )
    target_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="exchange_rates_target",
        verbose_name=_("Target Currency"),
        help_text=_("Sarafu ambayo kiwango kinatumika kubadilisha")
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name=_("Exchange Rate"),
        help_text=_("Kiwango cha kubadilisha kutoka sarafu ya msingi hadi sarafu lengwa")
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Source"),
        help_text=_("Chanzo cha kiwango hiki (mfano: Forex API, Bank XYZ)")
    )
    effective_date = models.DateField(
        verbose_name=_("Effective Date"),
        help_text=_("Tarehe ambayo kiwango hiki kinaanza kutumika")
    )

    class Meta:
        verbose_name = _("Exchange Rate")
        verbose_name_plural = _("Exchange Rates")
        unique_together = ("base_currency", "target_currency", "effective_date")
        ordering = ["-effective_date"]

    def __str__(self):
        return _(
            "{base} → {target} @ {rate} (kutoka {date})"
        ).format(
            base=self.base_currency,
            target=self.target_currency,
            rate=self.rate,
            date=self.effective_date
        )