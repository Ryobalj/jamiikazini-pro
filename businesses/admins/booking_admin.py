# businesses/admins/booking_admin.py

from django.contrib import admin
from businesses.models.booking import Booking, BookingLog


class BookingLogInline(admin.TabularInline):
    """Displays Booking Logs as an inline within the Booking Admin."""
    model = BookingLog
    extra = 0
    readonly_fields = ("action", "actor_type", "user", "ip_address", "user_agent", "metadata", "created_at")
    can_delete = False
    ordering = ("-created_at",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin configuration for Booking."""
    list_display = (
        "service",
        "client",
        "status",
        "payment_status",
        "scheduled_datetime",
        "actual_start_time",
        "actual_end_time",
    )
    list_filter = ("status", "payment_status", "scheduled_datetime")
    search_fields = ("client__email", "service__name", "payment_reference")
    inlines = [BookingLogInline]
    readonly_fields = ("estimated_end_time",)


@admin.register(BookingLog)
class BookingLogAdmin(admin.ModelAdmin):
    """Admin configuration for Booking Logs."""
    list_display = ("booking", "actor_type", "user", "action", "created_at")
    list_filter = ("actor_type", "action", "created_at")
    search_fields = ("booking__service__name", "user__email", "action")
    readonly_fields = ("metadata", "created_at")
    ordering = ("-created_at",)