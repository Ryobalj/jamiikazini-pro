# payments/models/payment_link.py

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel
from django.core.exceptions import ValidationError
from payments.models.currency import Currency

class PaymentLink(UUIDModel, TimeStampedModel):
    """Model for creating shareable payment links"""
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Inatumika')
        USED = 'USED', _('Imetumika')
        EXPIRED = 'EXPIRED', _('Imekwisha')
        CANCELLED = 'CANCELLED', _('Imesitishwa')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_links_created',
        verbose_name=_("Imetengenezwa Na"),
        help_text=_("Mtumiaji aliyeunda kiungo hiki cha malipo")
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Kiasi"),
        help_text=_("Kiasi cha malipo kinachohitajika")
    )
    
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_("Sarafu"),
        help_text=_("Aina ya sarafu ya malipo")
    )
    
    description = models.CharField(
        max_length=500,
        verbose_name=_("Maelezo"),
        help_text=_("Maelezo mafupi kuhusu malipo")
    )
    
    link_code = models.CharField(
        max_length=16,
        unique=True,
        verbose_name=_("Msimbo wa Kiungo"),
        help_text=_("Msimbo wa kipekee wa kiungo cha malipo")
    )
    
    expires_at = models.DateTimeField(
        verbose_name=_("Inakwisha Tarehe"),
        help_text=_("Tarehe na wakati kiungo kitakapokwisha kuwa halali")
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_("Hali"),
        help_text=_("Hali ya kiungo cha malipo")
    )
    
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_links_used',
        verbose_name=_("Imetumika Na"),
        help_text=_("Mtumiaji aliyetumia kiungo hiki cha malipo")
    )
    
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Imetumika Tarehe"),
        help_text=_("Tarehe na wakati kiungo kilipotumika")
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
        help_text=_("Taarifa za ziada kuhusu kiungo hiki")
    )
    
    allowed_methods = models.JSONField(
        default=list,
        verbose_name=_("Mbinu Zilizoruhusiwa"),
        help_text=_("Aina za mbinu za malipo zilizoruhusiwa")
    )

    class Meta:
        db_table = 'payment_links'
        verbose_name = _("Kiungo cha Malipo")
        verbose_name_plural = _("Viungo vya Malipo")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['link_code']),
            models.Index(fields=['expires_at', 'status']),
            models.Index(fields=['created_by', 'status']),
        ]

    def __str__(self):
        return f"Kiungo {self.link_code} - {self.amount} {self.currency.code}"

    def clean(self):
        """Hakikisha data ya kiungo cha malipo iko sahihi"""
        errors = {}
        
        # Hakikisha tarehe ya kumalizika
        if self.expires_at and self.expires_at <= timezone.now():
            errors['expires_at'] = _("Tarehe ya kumalizika lazima iwe baada ya sasa")
        
        # Hakikisha kiasi
        if self.amount <= 0:
            errors['amount'] = _("Kiasi lazima kiwe zaidi ya sifuri")
        
        if errors:
            raise ValidationError(errors)

    @property
    def is_expired(self):
        """Angalia ikiwa kiungo kimekwisha"""
        return self.expires_at and self.expires_at < timezone.now()

    @property
    def is_usable(self):
        """Angalia ikiwa kiungo kinaweza kutumiwa"""
        return (self.status == self.Status.ACTIVE and 
                not self.is_expired and 
                not self.used_by)

    def get_absolute_url(self):
        """Pata URL kamili ya kiungo cha malipo"""
        from django.conf import settings
        base_url = getattr(settings, 'FRONTEND_URL', 'https://app.jamiikazini.com')
        return f"{base_url}/pay/{self.link_code}"

    def mark_as_used(self, user, payment_reference):
        """Weka kiungo kama kilichotumiwa"""
        self.status = self.Status.USED
        self.used_by = user
        self.used_at = timezone.now()
        self.payment_reference = payment_reference
        self.save()

    def mark_as_expired(self):
        """Weka kiungo kama kilichokwisha"""
        self.status = self.Status.EXPIRED
        self.save()

    def extend_expiry(self, new_expires_at):
        """Panua tarehe ya kumalizika ikiwa bado haijatumiwa"""
        if self.status == self.Status.ACTIVE and not self.used_by:
            self.expires_at = new_expires_at
            self.save()