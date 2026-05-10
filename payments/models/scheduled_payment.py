# payments/models/scheduled_payment.py

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel
from django.core.exceptions import ValidationError
from payments.models.currency import Currency
from payments.models.paymentmethod import PaymentMethod
from jamiiwallet.models.wallet import Wallet

class ScheduledPayment(UUIDModel, TimeStampedModel):
    """Model for scheduling future payments"""
    
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Imerasimiwa')
        PROCESSING = 'PROCESSING', _('Inafanyika')
        COMPLETED = 'COMPLETED', _('Imekamilika')
        FAILED = 'FAILED', _('Imeshindwa')
        CANCELLED = 'CANCELLED', _('Imesitishwa')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_payments_created',
        verbose_name=_("Imetengenezwa Na"),
        help_text=_("Mtumiaji aliyeunda malipo yaliyorasimiwa")
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Kiasi"),
        help_text=_("Kiasi cha malipo")
    )
    
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_("Sarafu"),
        help_text=_("Aina ya sarafu ya malipo")
    )
    
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.CASCADE,
        verbose_name=_("Mbinu ya Malipo"),
        help_text=_("Mbinu ya malipo itakayotumika")
    )
    
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_payments_received',
        verbose_name=_("Mtumiaji Anayepokea"),
        help_text=_("Mtumiaja atakayepokea malipo")
    )
    
    recipient_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Mkoba Anayepokea"),
        help_text=_("Mkoba utakayopokea malipo (hiari)")
    )
    
    schedule_date = models.DateTimeField(
        verbose_name=_("Tarehe Iliyorasmishiwa"),
        help_text=_("Tarehe na wakati malipo yatafanyika")
    )
    
    description = models.CharField(
        max_length=500,
        verbose_name=_("Maelezo"),
        help_text=_("Maelezo kuhusu malipo yaliyorasmishiwa")
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name=_("Hali"),
        help_text=_("Hali ya malipo yaliyorasmishiwa")
    )
    
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Rejea ya Malipo"),
        help_text=_("Nambari ya kumbukumbu ya malipo yaliyofanyika")
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Taarifa za ziada kuhusu malipo yaliyorasmishiwa")
    )
    
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Imetekelezwa Tarehe"),
        help_text=_("Tarehe na wakati malipo yalipotekelezwa")
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Imesitishwa Tarehe"),
        help_text=_("Tarehe na wakati malipo yalipositishwa")
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Ujumbe wa Hitilafu"),
        help_text=_("Maelezo ya hitilafu ikiwa malipo yameshindwa")
    )

    class Meta:
        db_table = 'payment_scheduled'
        verbose_name = _("Malipo Yaliyorasmishiwa")
        verbose_name_plural = _("Malipo Yaliyorasmishiwa")
        ordering = ['schedule_date']
        indexes = [
            models.Index(fields=['schedule_date', 'status']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['recipient_user', 'status']),
        ]

    def __str__(self):
        return f"Malipo Yaliyorasmishiwa {self.id} - {self.amount} {self.currency.code}"

    def clean(self):
        """Hakikisha data ya malipo yaliyopangwa iko sahihi"""
        errors = {}
        
        # Hakikisha tarehe ya kurasmishwa
        if self.schedule_date and self.schedule_date <= timezone.now():
            errors['schedule_date'] = _("Tarehe ya kurasmishwa lazima iwe baada ya sasa")
        
        # Hakikisha kiasi
        if self.amount <= 0:
            errors['amount'] = _("Kiasi lazima kiwe zaidi ya sifuri")
        
        # Hakikisha mpokeaji
        if self.created_by == self.recipient_user:
            errors['recipient_user'] = _("Huwezi kujirasmishia malipo")
        
        if errors:
            raise ValidationError(errors)

    @property
    def is_due(self):
        """Angalia ikiwa malipo yamefika wakati wake"""
        return (self.status == self.Status.SCHEDULED and 
                self.schedule_date <= timezone.now())

    @property
    def can_be_cancelled(self):
        """Angalia ikiwa malipo yanaweza kusitishwa"""
        return self.status in [self.Status.SCHEDULED, self.Status.PROCESSING]

    def mark_processing(self):
        """Weka kama inasindika"""
        self.status = self.Status.PROCESSING
        self.save()

    def mark_completed(self, payment_reference):
        """Weka kama yamekamilika"""
        self.status = self.Status.COMPLETED
        self.payment_reference = payment_reference
        self.executed_at = timezone.now()
        self.save()

    def mark_failed(self, error_message):
        """Weka kama yameshindwa"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.executed_at = timezone.now()
        self.save()

    def cancel(self):
        """Sitisha malipo yaliyopangwa"""
        if self.can_be_cancelled:
            self.status = self.Status.CANCELLED
            self.cancelled_at = timezone.now()
            self.save()