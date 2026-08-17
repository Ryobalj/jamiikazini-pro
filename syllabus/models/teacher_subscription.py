# syllabus/models/teacher_subscription.py

from django.db import models
from django.utils import timezone
from datetime import timedelta
from kiini.models.base import UUIDModel, TimeStampedModel


class TeacherSubscription(UUIDModel, TimeStampedModel):
    """
    Gates full document generation/download (Azimio la Kazi, Andalio la
    Somo, Nukuu za Somo) behind a paid monthly subscription. The teacher's
    JamiiWallet balance is debited automatically each renewal cycle (see
    syllabus/services/subscription_service.py and
    jamiitasks/tasks/syllabus_subscription_tasks.py) — no fresh mobile
    money prompt needed each cycle as long as the wallet stays funded.
    """

    class ChargeStatus(models.TextChoices):
        NEVER_CHARGED = "never_charged", "Never Charged"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed (insufficient balance)"

    workstation = models.OneToOneField(
        "syllabus.TeacherWorkStation",
        on_delete=models.CASCADE,
        related_name="subscription",
        help_text="The teacher work station this subscription grants full document access to."
    )
    monthly_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=5000,
        help_text="Monthly fee in the wallet's currency (TZS)."
    )
    is_active = models.BooleanField(
        default=False,
        help_text="True only while a paid, unexpired period is in effect."
    )
    current_period_end = models.DateField(
        null=True, blank=True,
        help_text="Date the current paid period expires. Renewed automatically on/after this date if the wallet has sufficient balance."
    )
    last_charge_attempt_at = models.DateTimeField(null=True, blank=True)
    last_charge_status = models.CharField(
        max_length=20, choices=ChargeStatus.choices, default=ChargeStatus.NEVER_CHARGED
    )
    last_failure_reason = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Teacher Subscription"
        verbose_name_plural = "Teacher Subscriptions"

    def __str__(self):
        return f"Subscription({self.workstation.school_name}) - {'active' if self.is_valid else 'inactive'}"

    @property
    def is_valid(self) -> bool:
        """Whether this subscription currently grants full access."""
        if not self.is_active or not self.current_period_end:
            return False
        return self.current_period_end >= timezone.localdate()

    def extend_period(self, days: int = 30):
        today = timezone.localdate()
        base = self.current_period_end if (self.current_period_end and self.current_period_end > today) else today
        self.current_period_end = base + timedelta(days=days)
        self.is_active = True
