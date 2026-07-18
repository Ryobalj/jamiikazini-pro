# billpay/models/bill_payment.py

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from billpay.models.biller import Biller
from payments.models.currency import Currency
from jamiiwallet.models.transaction import Transaction
from security.helpers.encryption import encrypt_data, decrypt_data


class BillPaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")


class BillPayment(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bill_payments",
    )
    biller = models.ForeignKey(Biller, on_delete=models.PROTECT, related_name="payments")
    account_number = models.CharField(
        max_length=50, help_text=_("Namba ya mita/simu/decoder inayolipiwa."),
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="bill_payments")
    status = models.CharField(
        max_length=20, choices=BillPaymentStatus.choices, default=BillPaymentStatus.PENDING,
    )
    # WITHDRAWAL transaction inayoondoa fedha kwenye wallet - fedha zinatoka
    # kabisa nje ya Jamiikazini (kwenda kwa biller), sawa na Withdrawal/CashOut,
    # si PAYMENT (ambayo inahitaji counterparty ya mtumiaji mwingine wa mfumo).
    wallet_transaction = models.OneToOneField(
        Transaction, null=True, blank=True, on_delete=models.SET_NULL, related_name="bill_payment",
    )
    external_reference = models.CharField(max_length=100, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    # LUKU token n.k. - thamani ya kifedha, inahifadhiwa encrypted sawa na
    # Transaction._receipt / User._national_id.
    _token_or_receipt = models.TextField(null=True, blank=True, db_column="token_or_receipt")

    class Meta:
        verbose_name = _("Bill Payment")
        verbose_name_plural = _("Bill Payments")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"BillPayment({self.biller.name}, {self.account_number}, {self.status})"

    @property
    def token_or_receipt(self):
        return decrypt_data(self._token_or_receipt) if self._token_or_receipt else None

    @token_or_receipt.setter
    def token_or_receipt(self, value):
        self._token_or_receipt = encrypt_data(value) if value else None
