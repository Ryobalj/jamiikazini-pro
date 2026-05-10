# payments/models/payment_report.py

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel
from django.core.exceptions import ValidationError

class PaymentReport(UUIDModel, TimeStampedModel):
    """Model for advanced payment reporting with dynamic data generation"""
    
    class ReportType(models.TextChoices):
        TRANSACTION_SUMMARY = 'TRANSACTION_SUMMARY', _('Muhtasari wa Malipo')
        REVENUE_ANALYSIS = 'REVENUE_ANALYSIS', _('Uchambuzi wa Mapato')
        USER_ACTIVITY = 'USER_ACTIVITY', _('Shughuli za Watumiaji')
        GATEWAY_PERFORMANCE = 'GATEWAY_PERFORMANCE', _('Utendaji wa Mfumo wa Malipo')
        DAILY_SUMMARY = 'DAILY_SUMMARY', _('Muhtasari wa Kila Siku')
        CUSTOM = 'CUSTOM', _('Ripoti Maalum')

    class Status(models.TextChoices):
        GENERATING = 'GENERATING', _('Inatengenezwa')
        COMPLETED = 'COMPLETED', _('Imekamilika')
        FAILED = 'FAILED', _('Imeshindwa')
        CANCELLED = 'CANCELLED', _('Imesitishwa')

    # Sehemu kuu
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Mtumiaji"),
        help_text=_("Mtumiaji aliyeomba ripoti hii")
    )
    report_type = models.CharField(
        max_length=50,
        choices=ReportType.choices,
        verbose_name=_("Aina ya Ripoti"),
        help_text=_("Aina ya ripoti inayotengenezwa")
    )
    
    # Muda wa data ya ripoti
    start_date = models.DateTimeField(
        verbose_name=_("Tarehe ya Kuanzia"),
        help_text=_("Tarehe ya mwanzo wa data ya ripoti")
    )
    end_date = models.DateTimeField(
        verbose_name=_("Tarehe ya Mwisho"),
        help_text=_("Tarehe ya mwisho wa data ya ripoti")
    )
    
    # Vigezo na vichujio
    filters = models.JSONField(
        default=dict,
        verbose_name=_("Vichujio"),
        help_text=_("Vigezo na vichujio vya ripoti")
    )
    
    # Data na matokeo ya ripoti
    report_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Data ya Ripoti"),
        help_text=_("Data iliyokusanywa na kuchambuliwa")
    )
    
    # Muhtasari wa ripoti
    summary = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Muhtasari"),
        help_text=_("Muhtasari wa ripoti na viashiria muhimu")
    )
    
    # Hali na ufuatiliaji wa maendeleo
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING,
        verbose_name=_("Hali"),
        help_text=_("Hali ya utengenezaji wa ripoti")
    )
    progress_percentage = models.IntegerField(
        default=0,
        verbose_name=_("Asilimia ya Utekelezaji"),
        help_text=_("Asilimia ya utengenezaji wa ripoti")
    )
    
    # Matokeo na utoaji
    download_url = models.URLField(
        blank=True,
        verbose_name=_("URL ya Kupakua"),
        help_text=_("Kiungo cha kupakua ripoti kamili")
    )
    file_format = models.CharField(
        max_length=10,
        default='JSON',
        choices=[('JSON', 'JSON'), ('CSV', 'CSV'), ('PDF', 'PDF'), ('EXCEL', 'Excel')],
        verbose_name=_("Umbizo la Faili"),
        help_text=_("Umbizo la faili ya ripoti")
    )
    
    # Usimamizi wa makosa
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Ujumbe wa Hitilafu"),
        help_text=_("Maelezo ya hitilafu ikiwa ripoti imeshindwa")
    )
    
    # Nyakati
    generated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Tarehe ya Kutengenezwa"),
        help_text=_("Tarehe na wakati ripoti ilipotengenezwa")
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Tarehe ya Kukoma"),
        help_text=_("Tarehe ripoti itakapokoma kuwa halali")
    )

    class Meta:
        verbose_name = _("Ripoti ya Malipo")
        verbose_name_plural = _("Ripoti za Malipo")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['user', 'report_type', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return _("Ripoti ya {type} - {user} ({status})").format(
            type=self.get_report_type_display(),
            user=self.user.get_full_name() if self.user else "Haijulikani",
            status=self.get_status_display()
        )

    def clean(self):
        """Hakikisha vigezo vya ripoti viko sahihi"""
        errors = {}
        
        # Hakikisha muda
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                errors['start_date'] = _("Tarehe ya kuanzia lazima iwe kabla ya tarehe ya mwisho")
            
            # Wekea kikomo kipindi cha ripoti hadi mwaka mmoja
            if (self.end_date - self.start_date).days > 365:
                errors['end_date'] = _("Kipindi cha ripoti hakiwezi kuzidi mwaka mmoja")
        
        # Hakikisha asilimia ya maendeleo
        if self.progress_percentage < 0 or self.progress_percentage > 100:
            errors['progress_percentage'] = _("Asilimia ya utekelezaji lazima iwe kati ya 0 na 100")
        
        if errors:
            raise ValidationError(errors)

    @property
    def is_ready(self):
        """Angalia ikiwa ripoti iko tayari kwa upakuaji"""
        return self.status == self.Status.COMPLETED and self.report_data is not None

    @property
    def is_expired(self):
        """Angalia ikiwa ripoti imekwisha"""
        return self.expires_at and self.expires_at < timezone.now()

    def get_summary_statistics(self):
        """Pata takwimu muhimu kutoka kwa muhtasari wa ripoti"""
        if not self.summary:
            return {}
        
        return {
            'total_transactions': self.summary.get('total_transactions', 0),
            'total_amount': self.summary.get('total_amount', 0),
            'success_rate': self.summary.get('success_rate', 0),
            'average_transaction': self.summary.get('average_transaction', 0),
        }

    def mark_completed(self, report_data, summary_data):
        """Weka ripoti kama iliyokamilika na data"""
        self.status = self.Status.COMPLETED
        self.report_data = report_data
        self.summary = summary_data
        self.progress_percentage = 100
        self.generated_at = timezone.now()
        
        # Weka kikomo cha siku 7 kutoka utengenezaji
        self.expires_at = timezone.now() + timezone.timedelta(days=7)
        self.save()

    def mark_failed(self, error_message):
        """Weka ripoti kama imeshindwa"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.progress_percentage = 0
        self.save()