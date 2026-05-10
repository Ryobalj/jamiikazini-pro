from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.service import Service
from accounts.models import User


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    CANCELLED = "CANCELLED", _("Cancelled")
    COMPLETED = "COMPLETED", _("Completed")


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PAID = "PAID", _("Paid")
    FAILED = "FAILED", _("Failed")


class Booking(UUIDModel, TimeStampedModel):
    """
    Represents a client's booking for a service.
    Handles status, payment status, actual times, and cancellation reasons.
    """
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name=_("Client"),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name=_("Service"),
    )
    scheduled_datetime = models.DateTimeField(
        verbose_name=_("Scheduled Date & Time"),
        help_text=_("The date and time the service is booked for."),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Client Notes"),
        help_text=_("Additional instructions or information from the client."),
    )
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        verbose_name=_("Booking Status"),
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_("Payment Status"),
    )
    actual_start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual Start Time"),
    )
    actual_end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual End Time"),
    )
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Cancellation Reason"),
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Payment Reference"),
    )

    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "payment_status"]),
            models.Index(fields=["scheduled_datetime"]),
        ]

    @property
    def estimated_end_time(self):
        """Calculate estimated end time based on service.duration_minutes."""
        from datetime import timedelta
        return self.scheduled_datetime + timedelta(minutes=self.service.duration_minutes)

    def save(self, *args, **kwargs):
        """Validation for actual_start_time and actual_end_time"""
        if self.actual_start_time and self.actual_end_time:
            if self.actual_end_time <= self.actual_start_time:
                raise ValidationError(_("Muda wa mwisho lazima uwe baada ya muda wa kuanza"))
        super().save(*args, **kwargs)

    def __str__(self):
        """Better identifier that won't break when using custom User model."""
        identifier = self.client.full_name or self.client.email
        return f"{self.service.name} for {identifier} ({self.get_status_display()})"


# =================== Booking Log Model ===================


class ActorType(models.TextChoices):
    CLIENT = "CLIENT", _("Client")
    OWNER = "OWNER", _("Business Owner")
    STAFF = "STAFF", _("Business Staff")
    SYSTEM = "SYSTEM", _("System")


class BookingLog(UUIDModel, TimeStampedModel):
    """
    Keeps track of status changes and significant events for Bookings.
    Provides a trail of what happened, by whom, and when.
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name=_("Booking"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_logs",
        verbose_name=_("User"),
    )
    actor_type = models.CharField(
        max_length=20,
        choices=ActorType.choices,
        default=ActorType.SYSTEM,
        verbose_name=_("Actor Type"),
        help_text=_("What role performed this action (Client, Owner, Staff, System)?"),
    )
    action = models.CharField(
        max_length=30,
        verbose_name=_("Action"),
        help_text=_("Action performed on the booking (e.g., CREATED, CONFIRMED, CANCELLED)."),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("User Agent"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Additional Context or Data"),
        help_text=_("Additional context or data related to the action."),
    )

    class Meta:
        verbose_name = _("Booking Log")
        verbose_name_plural = _("Booking Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["booking", "action"]),
            models.Index(fields=["actor_type"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        """Ensure metadata is always a dict."""
        if not isinstance(self.metadata, dict):
            self.metadata = {}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking} - {self.action} by System"