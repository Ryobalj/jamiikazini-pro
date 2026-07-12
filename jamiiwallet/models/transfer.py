# jamiiwallet/models/transfer.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel

from jamiiwallet.models.transaction import Transaction

User = settings.AUTH_USER_MODEL


class Transfer(UUIDModel, TimeStampedModel):
    """
    Uhamishaji wa salio kutoka wallet ya user mmoja kwenda mwingine (P2P), ndani ya
    mfumo (hauhitaji gateway ya nje). Huundwa Transaction MBILI zinazohusiana
    (moja kwa mtumaji - debit, moja kwa mpokeaji - credit) kwa uwazi wa historia
    ya kila upande.
    """

    class TransferStatus(models.TextChoices):
        INITIATED = 'INITIATED', _('Initiated')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transfers_sent',
        help_text=_('User anayetuma pesa')
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transfers_received',
        help_text=_('User anayepokea pesa')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_('Kiasi cha kutuma')
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=_('Ujumbe wa hiari kwa mpokeaji')
    )

    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.INITIATED
    )

    reference = models.CharField(
        max_length=64,
        unique=True,
        help_text=_('Unique reference kwa uhamisho huu')
    )

    sender_transaction = models.OneToOneField(
        Transaction,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='transfer_sent'
    )

    recipient_transaction = models.OneToOneField(
        Transaction,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='transfer_received'
    )

    failure_reason = models.CharField(max_length=255, blank=True, default='')

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Transfer')
        verbose_name_plural = _('Transfers')

    def __str__(self):
        return f'Transfer {self.reference} - {self.amount} ({self.status})'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('Amount must be greater than zero.'))
        if self.sender_id and self.recipient_id and self.sender_id == self.recipient_id:
            raise ValidationError(_('Cannot transfer money to yourself.'))

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from jamiitasks.tasks.wallet import process_transfer_transaction
            process_transfer_transaction.delay(str(self.id))

    def generate_reference(self):
        import uuid
        return f'TRF-{uuid.uuid4().hex.upper()[:12]}'

    def mark_completed(self, sender_txn: Transaction, recipient_txn: Transaction):
        self.status = self.TransferStatus.COMPLETED
        self.sender_transaction = sender_txn
        self.recipient_transaction = recipient_txn
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'sender_transaction', 'recipient_transaction', 'completed_at'])

    def mark_failed(self, reason: str = ''):
        self.status = self.TransferStatus.FAILED
        self.failure_reason = reason[:255]
        self.save(update_fields=['status', 'failure_reason'])
