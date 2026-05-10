# payments/admin/payment_failure_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.payment_failure import PaymentFailure

@admin.register(PaymentFailure)
class PaymentFailureAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "currency", "retries", "created_at")
    list_filter = ("currency", "retries", "created_at")
    search_fields = ("reference", "user__full_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (_("Payment Failure Details"), {
            "fields": ("user", "amount", "currency", "reference", "reason", "retries")
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
        }),
    )