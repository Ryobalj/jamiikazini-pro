# jamiiwallet/models/transaction.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from payments.models.currency import Currency

from security.helpers.encryption import encrypt_data, decrypt_data

User = settings.AUTH_USER_MODEL


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        TOP_UP = 'TOP_UP', _('Top Up')
        WITHDRAWAL = 'WITHDRAWAL', _('Withdrawal')
        TRANSFER = 'TRANSFER', _('Transfer')
        PAYMENT = 'PAYMENT', _('Payment')
        REFUND = 'REFUND', _('Refund')

    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REVERSED = 'REVERSED', _('Reversed')

    wallet = models.ForeignKey(
        'jamiiwallet.Wallet',
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text=_('Wallet associated with this transaction'),
        null=True, blank=True
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Currency associated with this Transaction",
    )

    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_initiated',
        help_text=_('User who initiated the transaction')
    )

    counterparty = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_counterparty',
        help_text=_('Counterparty user involved in this transaction, if applicable')
    )

    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)

    amount = models.DecimalField(max_digits=18, decimal_places=2)

    # Idempotency key (optional but unique if provided)
    idempotency_key = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Key used to enforce idempotency for this transaction')
    )

    # Encrypted unique reference
    _reference = models.CharField(max_length=512, unique=True, db_column="reference")

    # Free-form transaction metadata (source_txn_id, merchant_id, channel...)
    metadata = models.JSONField(default=dict, blank=True)

    # Encrypted receipt data
    _receipt = models.TextField(null=True, blank=True, db_column="receipt")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    reversed_transaction = models.OneToOneField(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reversal_of'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'transaction_type', 'status']),
            models.Index(fields=['idempotency_key']),
        ]
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')

    def __str__(self):
        return f'{self.transaction_type} #{self.reference} ({self.status}) - {self.amount}'

    # -------------------
    # Encrypted properties
    # -------------------
    @property
    def reference(self):
        return decrypt_data(self._reference)

    @reference.setter
    def reference(self, value: str):
        self._reference = encrypt_data(value)

    @property
    def receipt(self):
        return None if not self._receipt else decrypt_data(self._receipt)

    @receipt.setter
    def receipt(self, value: dict):
        import json
        self._receipt = encrypt_data(json.dumps(value))

    # -------------------
    # Validation & utils
    # -------------------
    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('Transaction amount must be positive and greater than zero.'))

        if self.status == self.TransactionStatus.REVERSED and not self.reversed_transaction:
            raise ValidationError(_('Reversed transactions must reference the original transaction.'))

        if self.reversed_transaction and self.status != self.TransactionStatus.REVERSED:
            raise ValidationError(_('Reversed transaction must have status set to REVERSED.'))

    def save(self, *args, **kwargs):
        # Auto-generate reference if missing
        if not self._reference:
            self.reference = self.generate_unique_reference()
        super().save(*args, **kwargs)

    def generate_unique_reference(self):
        import uuid
        return uuid.uuid4().hex.upper()

    def mark_completed(self):
        self.status = self.TransactionStatus.COMPLETED
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])

    def mark_failed(self):
        self.status = self.TransactionStatus.FAILED
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])

    def mark_reversed(self, reversed_txn: 'Transaction'):
        self.status = self.TransactionStatus.REVERSED
        self.reversed_transaction = reversed_txn
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'reversed_transaction', 'updated_at'])

    @property
    def user(self):
        return self.initiated_by

    @user.setter
    def user(self, value):
        self.initiated_by = value

    # -------------------
    # Currency helpers
    # -------------------
    @property
    def wallet_currency(self):
        """Return the Currency object of the wallet linked to this transaction (optional reference)."""
        if self.wallet:
            return self.wallet.currency
        return None

    @property
    def currency_code(self):
        """Return the currency code (e.g., 'TZS') of the transaction currency."""
        return self.currency.code if self.currency else None

    @property
    def currency_symbol(self):
        """Return the currency symbol (e.g., 'Tsh') of the transaction currency."""
        return self.currency.symbol if self.currency else ""

    @property
    def amount_in_default_currency(self):
        """
        Return the transaction amount converted to default currency
        using currency_service.convert_to_default().
        """
        if not self.currency:
            return self.amount  # fallback if currency missing
        return convert_to_default(self.amount, self.currency.code)