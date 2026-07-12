# jamiiwallet/models/payment_request.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel

from jamiiwallet.models.transfer import Transfer

User = settings.AUTH_USER_MODEL


class PaymentRequest(UUIDModel, TimeStampedModel):
    """
    Ombi la kuomba pesa kutoka kwa user mwingine ('Omba Pesa'). Likikubaliwa na
    mlipaji (payer), huzalisha Transfer halisi (payer -> requester) kwa kutumia
    injini ile ile iliyothibitika ya Transfer.
    """

    class RequestStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        DECLINED = 'DECLINED', _('Declined')
        CANCELLED = 'CANCELLED', _('Cancelled')

    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_requests_made',
        help_text=_('User anayeomba pesa')
    )

    payer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_requests_received',
        help_text=_('User anayeombwa alipe')
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    note = models.CharField(max_length=255, blank=True, default='')

    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )

    reference = models.CharField(max_length=64, unique=True)

    resulting_transfer = models.OneToOneField(
        Transfer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='payment_request'
    )

    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Payment Request')
        verbose_name_plural = _('Payment Requests')

    def __str__(self):
        return f'PaymentRequest {self.reference} - {self.amount} ({self.status})'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('Amount must be greater than zero.'))
        if self.requester_id and self.payer_id and self.requester_id == self.payer_id:
            raise ValidationError(_('Cannot request money from yourself.'))

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from kiini.helpers.notification_helper import notify_user
            notify_user(
                self.payer,
                f"{self.requester.full_name} anaomba {self.amount} kutoka kwako.",
            )

    def generate_reference(self):
        import uuid
        return f'REQ-{uuid.uuid4().hex.upper()[:12]}'

    def accept(self) -> Transfer:
        """Mlipaji anakubali - huzalisha Transfer halisi (payer -> requester)."""
        if self.status != self.RequestStatus.PENDING:
            raise ValidationError(_('Request is not pending.'))
        transfer = Transfer.objects.create(
            sender=self.payer,
            recipient=self.requester,
            amount=self.amount,
            note=self.note or f"Malipo ya ombi {self.reference}",
        )
        # Transfer.save() huchakata process_transfer_transaction papo hapo (EAGER
        # mode) kwenye fetch tofauti - refresh ili tuone status ya kweli kabla ya
        # kuamua kama ombi hili limekamilika au limeshindwa (mfano salio halitoshi).
        transfer.refresh_from_db()
        if transfer.status != Transfer.TransferStatus.COMPLETED:
            raise ValidationError(
                _('Malipo hayakukamilika: %(reason)s') % {'reason': transfer.failure_reason or _('haijulikani')}
            )

        self.status = self.RequestStatus.ACCEPTED
        self.resulting_transfer = transfer
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'resulting_transfer', 'responded_at'])
        from kiini.helpers.notification_helper import notify_user
        notify_user(self.requester, f"{self.payer.full_name} amekubali ombi lako la {self.amount}.")
        return transfer

    def decline(self):
        if self.status != self.RequestStatus.PENDING:
            raise ValidationError(_('Request is not pending.'))
        self.status = self.RequestStatus.DECLINED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        from kiini.helpers.notification_helper import notify_user
        notify_user(self.requester, f"{self.payer.full_name} amekataa ombi lako la {self.amount}.")

    def cancel(self):
        if self.status != self.RequestStatus.PENDING:
            raise ValidationError(_('Request is not pending.'))
        self.status = self.RequestStatus.CANCELLED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
