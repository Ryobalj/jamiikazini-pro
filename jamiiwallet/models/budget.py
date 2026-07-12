# jamiiwallet/models/budget.py

from datetime import timedelta

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel

from jamiiwallet.models.expense import ExpenseCategory


class BudgetPeriod(models.TextChoices):
    WEEKLY = 'WEEKLY', _('Kila Wiki')
    MONTHLY = 'MONTHLY', _('Kila Mwezi')
    YEARLY = 'YEARLY', _('Kila Mwaka')


class Budget(UUIDModel, TimeStampedModel):
    """
    Lengo la matumizi kwa kipindi fulani (kwa kundi maalum la gharama, au
    jumla ikiwa category haijawekwa). Hutumika kufuatilia kama mtumiaji
    amezidi matumizi aliyojipangia.
    """

    wallet = models.ForeignKey(
        'jamiiwallet.Wallet',
        on_delete=models.CASCADE,
        related_name='budgets',
        help_text=_('Wallet inayohusika na bajeti hii')
    )

    category = models.CharField(
        max_length=20,
        choices=ExpenseCategory.choices,
        null=True,
        blank=True,
        help_text=_('Kundi la gharama linalofuatiliwa; tupu = bajeti ya jumla (makundi yote)')
    )

    period = models.CharField(max_length=20, choices=BudgetPeriod.choices, default=BudgetPeriod.MONTHLY)

    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text=_('Kiwango cha juu cha matumizi'))

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Budget')
        verbose_name_plural = _('Budgets')

    def __str__(self):
        label = self.get_category_display() if self.category else _('Jumla')
        return f'{label} - {self.amount}/{self.period}'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('Amount must be greater than zero.'))

    def current_period_range(self):
        """Rudisha (start, end) ya kipindi cha sasa kulingana na 'period'."""
        today = timezone.now().date()
        if self.period == BudgetPeriod.WEEKLY:
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
        elif self.period == BudgetPeriod.YEARLY:
            start = today.replace(month=1, day=1)
            end = today.replace(month=12, day=31)
        else:  # MONTHLY
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end

    def spent_amount(self):
        """Jumla ya Expense kwenye kipindi cha sasa (na category, kama ipo)."""
        start, end = self.current_period_range()
        qs = self.wallet.expenses.filter(incurred_at__gte=start, incurred_at__lte=end)
        if self.category:
            qs = qs.filter(category=self.category)
        return qs.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def remaining_amount(self):
        return self.amount - self.spent_amount()

    @property
    def is_over_budget(self):
        return self.spent_amount() > self.amount
