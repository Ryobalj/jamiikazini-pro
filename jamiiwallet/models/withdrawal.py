# jamiiwallet/models/withdrawal.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel

from jamiiwallet.models.transaction import Transaction

User = settings.AUTH_USER_MODEL


class Withdrawal(UUIDModel, TimeStampedModel):
    """
    Ombi la kutoa salio kutoka wallet ya mfumo kwenda simu ya mteja (mobile money)
    kupitia PawaPay payout. Salio hupunguzwa (hold) mara ombi linapoundwa; likishindwa
    hurejeshwa (REVERSED).
    """

    class WithdrawalStatus(models.TextChoices):
        INITIATED = 'INITIATED', _('Initiated')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REVERSED = 'REVERSED', _('Reversed')  # payout ilishindwa, salio limerejeshwa

    class WithdrawalChannel(models.TextChoices):
        PAWAPAY = 'pawapay', _('PawaPay')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='withdrawals',
        help_text=_('User requesting the withdrawal')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_('Amount to withdraw')
    )

    status = models.CharField(
        max_length=20,
        choices=WithdrawalStatus.choices,
        default=WithdrawalStatus.INITIATED
    )

    channel = models.CharField(
        max_length=50,
        choices=WithdrawalChannel.choices,
        default=WithdrawalChannel.PAWAPAY,
        help_text=_('Payout channel or method')
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text=_('Recipient mobile money phone number (for PawaPay payouts)')
    )

    provider = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text=_('Mobile money provider / MNO code, e.g. TIGO_TZA (PawaPay)')
    )

    reference = models.CharField(
        max_length=64,
        unique=True,
        help_text=_('Unique reference for this withdrawal request')
    )

    transaction = models.OneToOneField(
        Transaction,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='withdrawal'
    )

    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Optional metadata for channel-specific data')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Time when withdrawal was completed')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Withdrawal')
        verbose_name_plural = _('Withdrawals')

    def __str__(self):
        return f'Withdrawal {self.reference} - {self.amount} ({self.status})'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('Amount must be greater than zero.'))

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from jamiitasks.tasks.wallet import process_withdrawal_transaction
            process_withdrawal_transaction.delay(str(self.id))

    def generate_reference(self):
        import uuid
        return f'WDR-{uuid.uuid4().hex.upper()[:12]}'

    def mark_processing(self):
        self.status = self.WithdrawalStatus.PROCESSING
        self.save(update_fields=['status'])

    def mark_completed(self, txn: Transaction = None):
        self.status = self.WithdrawalStatus.COMPLETED
        if txn is not None:
            self.transaction = txn
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'transaction', 'completed_at'])

    def mark_failed(self):
        self.status = self.WithdrawalStatus.FAILED
        self.save(update_fields=['status'])

    def mark_reversed(self):
        self.status = self.WithdrawalStatus.REVERSED
        self.save(update_fields=['status'])
