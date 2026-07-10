# jamiiwallet/models/topup.py

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel

from jamiiwallet.models.transaction import Transaction

User = settings.AUTH_USER_MODEL


class TopUp(UUIDModel, TimeStampedModel):
    class TopUpStatus(models.TextChoices):
        INITIATED = 'INITIATED', _('Initiated')
        PROCESSING = 'PROCESSING', _('Processing')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        FAILED = 'FAILED', _('Failed')

    class TopUpChannel(models.TextChoices):
        FLUTTERWAVE = 'flutterwave', _('Flutterwave')
        STRIPE = 'stripe', _('Stripe')
        PAWAPAY = 'pawapay', _('PawaPay')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topups',
        help_text=_('User requesting the top up')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_('Amount to top up')
    )

    status = models.CharField(
        max_length=20,
        choices=TopUpStatus.choices,
        default=TopUpStatus.INITIATED
    )

    channel = models.CharField(
        max_length=50,
        choices=TopUpChannel.choices,
        help_text=_('Payment channel or method')
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text=_('Payer mobile money phone number (for PawaPay deposits)')
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
        help_text=_('Unique reference for this topup request')
    )

    transaction = models.OneToOneField(
        Transaction,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='topup'
    )

    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Optional metadata for channel-specific data')
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Time when top up was confirmed')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Top Up')
        verbose_name_plural = _('Top Ups')

    def __str__(self):
        return f'TopUp {self.reference} - {self.amount} ({self.status})'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('Amount must be greater than zero.'))

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from jamiitasks.tasks.wallet import confirm_topup_transaction
            confirm_topup_transaction.delay(str(self.id))

    def generate_reference(self):
        import uuid
        return f'TPU-{uuid.uuid4().hex.upper()[:12]}'

    def mark_processing(self):
        self.status = self.TopUpStatus.PROCESSING
        self.save(update_fields=['status'])

    def mark_confirmed(self, txn: Transaction):
        self.status = self.TopUpStatus.CONFIRMED
        self.transaction = txn
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'transaction', 'confirmed_at'])

    def mark_failed(self):
        self.status = self.TopUpStatus.FAILED
        self.save(update_fields=['status'])