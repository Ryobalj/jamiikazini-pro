# jamiiwallet/models/expense.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel

User = settings.AUTH_USER_MODEL


class ExpenseCategory(models.TextChoices):
    FOOD = 'FOOD', _('Chakula')
    TRANSPORT = 'TRANSPORT', _('Usafiri')
    RENT = 'RENT', _('Kodi ya Nyumba/Ofisi')
    UTILITIES = 'UTILITIES', _('Umeme/Maji/Mtandao')
    SUPPLIES = 'SUPPLIES', _('Malighafi/Vifaa')
    SALARIES = 'SALARIES', _('Mishahara')
    TAX = 'TAX', _('Kodi ya Serikali')
    HEALTH = 'HEALTH', _('Afya')
    EDUCATION = 'EDUCATION', _('Elimu')
    OTHER = 'OTHER', _('Nyingine')


class Expense(UUIDModel, TimeStampedModel):
    """
    Gharama iliyoandikwa na mmiliki wa wallet (mfano ununuzi wa malighafi kwa
    fedha taslimu, nje ya mfumo) - inasaidia kuwa na picha kamili ya hesabu
    (mapato yanatoka kwenye Transaction za wallet moja kwa moja; gharama
    zinaandikwa hapa kwa mkono kwa kuwa si kila gharama inapita kwenye wallet).
    """

    wallet = models.ForeignKey(
        'jamiiwallet.Wallet',
        on_delete=models.CASCADE,
        related_name='expenses',
        help_text=_('Wallet inayohusika na gharama hii (ya mtu au ya biashara baadaye)')
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses_recorded',
        help_text=_('Aliyeandika gharama hii')
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    category = models.CharField(
        max_length=20,
        choices=ExpenseCategory.choices,
        default=ExpenseCategory.OTHER,
    )

    note = models.CharField(max_length=255, blank=True, default='')

    incurred_at = models.DateField(
        default=timezone.localdate,
        help_text=_('Tarehe halisi gharama ilipotokea (si tarehe ya kuandikwa)')
    )

    class Meta:
        ordering = ['-incurred_at', '-created_at']
        verbose_name = _('Expense')
        verbose_name_plural = _('Expenses')
        indexes = [
            models.Index(fields=['wallet', 'category', 'incurred_at']),
        ]

    def __str__(self):
        return f'{self.get_category_display()} - {self.amount} ({self.incurred_at})'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('Amount must be greater than zero.'))
