# payments/models/payment_failure.py

from django.db import models
from django.conf import settings
from kiini.models.base import UUIDModel, TimeStampedModel
from payments.models.currency import Currency
from django.utils.translation import gettext_lazy as _

class PaymentFailure(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Kiasi cha Malipo")
    )
    currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Sarafu")
    )
    reference = models.CharField(
        max_length=255,
        verbose_name=_("Rejea ya Malipo")
    )
    reason = models.TextField(
        default=_("Unknown error"),
        verbose_name=_("Sababu ya Kushindwa")
    )
    retries = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Idadi ya Jaribio")
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ('user', 'reference')
        ordering = ['-created_at']
        verbose_name = _("Kushindwa kwa Malipo")
        verbose_name_plural = _("Kushindwa kwa Malipo")

    def __str__(self):
        return f"PaymentFailure({self.reference}, {self.amount}, retries={self.retries})"

    def increment_retries(self):
        self.retries = models.F('retries') + 1
        self.save(update_fields=["retries"])
        # Refresh from DB to get updated value after F expression
        self.refresh_from_db(fields=["retries"])
