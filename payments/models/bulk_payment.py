# payments/models/bulk_payment.py

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel
from django.core.exceptions import ValidationError
from jamiiwallet.models.wallet import Wallet


class BulkPaymentTemplate(UUIDModel, TimeStampedModel):
    """Template for bulk payments that can be reused"""
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Imetengenezwa Na"),
        help_text=_("Mtumiaji aliyeunda template hii ya malipo mengi")
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Jina la Template"),
        help_text=_("Jina la kutambulisha template hii ya malipo mengi")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Maelezo"),
        help_text=_("Maelezo ya kina kuhusu template hii")
    )
    
    payments_data = models.JSONField(
        verbose_name=_("Data ya Malipo"),
        help_text=_("Orodha ya maagizo ya malipo na mpokeaji, kiasi, sarafu, nk")
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Taarifa za ziada za template")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Inatumika"),
        help_text=_("Ikiwa template hii inatumika na inaweza kutumiwa")
    )

    class Meta:
        db_table = 'payment_bulk_templates'
        verbose_name = _("Template ya Malipo Mengi")
        verbose_name_plural = _("Template za Malipo Mengi")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({len(self.payments_data)} malipo)"

    def clean(self):
        """Hakikisha data ya malipo iko sawa"""
        if not isinstance(self.payments_data, list):
            raise ValidationError({'payments_data': _("Data ya malipo lazima iwe orodha")})
        
        if len(self.payments_data) == 0:
            raise ValidationError({'payments_data': _("Data ya malipo haiwezi kuwa tupu")})
        
        if len(self.payments_data) > 1000:
            raise ValidationError({'payments_data': _("Haiwezi kuzidi malipo 1000 kwa template moja")})
        
        # Hakikisha kila malipo kwenye orodha
        for i, payment in enumerate(self.payments_data):
            if not isinstance(payment, dict):
                raise ValidationError({
                    'payments_data': _(f"Malipo katika nafasi {i} lazima iwe kamusi")
                })
            
            required_fields = ['recipient_user_id', 'amount']
            for field in required_fields:
                if field not in payment:
                    raise ValidationError({
                        'payments_data': _(f"Malipo katika nafasi {i} inakosa uga unaohitajika: {field}")
                    })
            
            # Hakikisha kiasi
            try:
                amount = float(payment['amount'])
                if amount <= 0:
                    raise ValidationError({
                        'payments_data': _(f"Malipo katika nafasi {i} kiasi si sahihi: {amount}")
                    })
            except (ValueError, TypeError):
                raise ValidationError({
                    'payments_data': _(f"Malipo katika nafasi {i} kiasi si muundo sahihi")
                })

    @property
    def total_payments(self):
        """Pata jumla ya idadi ya malipo kwenye template"""
        return len(self.payments_data) if self.payments_data else 0

    @property
    def total_amount(self):
        """Hesabu jumla ya kiasi kote kwa malipo yote"""
        if not self.payments_data:
            return 0.0
        try:
            return round(sum(float(payment.get('amount', 0)) for payment in self.payments_data), 2)
        except Exception:
            return 0.0


class BulkPaymentExecution(UUIDModel, TimeStampedModel):
    """Rekodi ya utekelezaji wa usindikaji wa malipo mengi"""
    
    class Status(models.TextChoices):
        PROCESSING = 'PROCESSING', _('Inasindika')
        COMPLETED = 'COMPLETED', _('Imekamilika')
        FAILED = 'FAILED', _('Imeshindwa')
        PARTIAL = 'PARTIAL', _('Mafanikio Ya Kiasi')

    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Imefanywa Na"),
        help_text=_("Mtumiaji aliyeiteketeza malipo haya mengi")
    )
    
    template = models.ForeignKey(
        BulkPaymentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Template"),
        help_text=_("Template iliyotumika kwa utekelezaji huu (ikiwepo)")
    )
    
    total_payments = models.IntegerField(
        verbose_name=_("Jumla ya Malipo"),
        help_text=_("Jumla ya idadi ya malipo yanayosindika")
    )
    
    successful_count = models.IntegerField(
        default=0,
        verbose_name=_("Idadi ya Mafanikio"),
        help_text=_("Idadi ya malipo yaliyofanikiwa kusindika")
    )
    
    failed_count = models.IntegerField(
        default=0,
        verbose_name=_("Idadi ya Kushindwa"),
        help_text=_("Idadi ya malipo yaliyoshindwa")
    )
    
    results = models.JSONField(
        default=list,
        verbose_name=_("Matokeo"),
        help_text=_("Matokeo ya kina kwa kila jaribio la usindikaji wa malipo")
    )
    
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Ufunguo wa Kuzuia Marudio"),
        help_text=_("Ufunguo wa kipekee wa kuzuia utekelezaji mara mbili")
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
        verbose_name=_("Hali"),
        help_text=_("Hali ya sasa ya utekelezaji wa malipo mengi")
    )
    
    executed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Imefanywa Tarehe"),
        help_text=_("Wakati malipo haya mengi yalipofanywa")
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Imekamilika Tarehe"),
        help_text=_("Wakati malipo haya mengi yalipokamilika kusindika")
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Taarifa za ziada za utekelezaji")
    )

    class Meta:
        db_table = 'payment_bulk_executions'
        verbose_name = _("Utekelezaji wa Malipo Mengi")
        verbose_name_plural = _("Utekelezaji wa Malipo Mengi")
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['executed_by', 'status']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['status', 'executed_at']),
        ]

    def __str__(self):
        return f"Utekelezaji {self.id} - {self.get_status_display()}"

    def clean(self):
        """Hakikisha data ya utekelezaji iko sahihi"""
        if (self.successful_count or 0) < 0 or (self.failed_count or 0) < 0:
            raise ValidationError(_("Hesabu haiwezi kuwa hasi"))
        
        total = self.total_payments or 0
        if (self.successful_count or 0) + (self.failed_count or 0) > total:
            raise ValidationError(_("Yaliyofanikiwa + yaliyoshindwa haiwezi kuzidi jumla ya malipo"))

    @property
    def success_rate(self):
        """Hesabu asilimia ya mafanikio kwa usalama"""
        total = self.total_payments or 0
        success = self.successful_count or 0

        if total <= 0:
            return 0.0

        try:
            return round((success / total) * 100, 2)
        except ZeroDivisionError:
            return 0.0

    @property
    def is_completed(self):
        """Angalia ikiwa utekelezaji umekamilika kabisa"""
        return self.status in [self.Status.COMPLETED, self.Status.FAILED, self.Status.PARTIAL]

    def mark_completed(self):
        """Weka utekelezaji kama uliokamilika na hali inayofaa"""
        total = self.total_payments or 0
        success = self.successful_count or 0

        if success >= total and total > 0:
            self.status = self.Status.COMPLETED
        elif success == 0:
            self.status = self.Status.FAILED
        else:
            self.status = self.Status.PARTIAL

        self.completed_at = timezone.now()
        self.save()