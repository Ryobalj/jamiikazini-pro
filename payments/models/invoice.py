# payments/models/invoice.py

from django.db import models
from kiini.models.base import TimeStampedModel
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from security.helpers.encryption import encrypt_data, decrypt_data


class InvoiceStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PAID = "PAID", _("Paid")
    CANCELLED = "CANCELLED", _("Cancelled")
    OVERDUE = "OVERDUE", _("Overdue")


class Invoice(TimeStampedModel):
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Invoice Number"),
        help_text=_("Nambari ya kipekee ya invoice")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_("User"),
        help_text=_("Mtumiaji aliyelipwa invoice hii")
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Amount"),
        help_text=_("Kiasi cha msingi cha invoice")
    )
    tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Tax"),
        help_text=_("Kodi inayolipwa juu ya kiasi")
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        verbose_name=_("Total Amount"),
        help_text=_("Jumla ya kiasi + kodi")
    )
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.PENDING,
        verbose_name=_("Status"),
        help_text=_("Hali ya invoice")
    )
    due_date = models.DateField(
        verbose_name=_("Due Date"),
        help_text=_("Tarehe ya mwisho ya kulipa")
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Paid At"),
        help_text=_("Tarehe na wakati ulipolipwa")
    )

    # 🔐 Encrypted description
    _description = models.TextField(
        blank=True,
        null=True,
        db_column="description",
        verbose_name=_("Description (Encrypted)"),
        help_text=_("Maelezo ya ziada kuhusu invoice (imehifadhiwa kwa usalama)")
    )

    @property
    def description(self):
        if not self._description:
            return None
        try:
            return decrypt_data(self._description)
        except Exception:
            return "[DECRYPTION FAILED]"

    @description.setter
    def description(self, value):
        if value is None:
            self._description = None
        else:
            self._description = encrypt_data(value)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices_created",
        verbose_name=_("Created By"),
        help_text=_("Mtumiaji aliyefanya invoice hii")
    )
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices_modified",
        verbose_name=_("Last Modified By"),
        help_text=_("Mtumiaji wa mwisho aliyeyabadilisha invoice hii")
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        unique_together = ('invoice_number', 'created_at')
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.get_status_display()}) for {self.user}"

    def save(self, *args, **kwargs):
        # Calculate total_amount = amount + tax
        self.total_amount = self.amount + self.tax

        # If invoice is overdue but not marked, update status automatically
        if self.status != InvoiceStatus.PAID and self.due_date < timezone.now().date():
            self.status = InvoiceStatus.OVERDUE

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return self.status == InvoiceStatus.OVERDUE

    @property
    def amount_due(self):
        if self.status == InvoiceStatus.PAID:
            return 0
        return self.total_amount

    def mark_as_paid(self, paid_at=None):
        self.status = InvoiceStatus.PAID
        self.paid_at = paid_at or timezone.now()
        self.save(update_fields=['status', 'paid_at'])