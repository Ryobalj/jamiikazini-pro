# payments/admin/payment_method_admin.py

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
import csv

from payments.models.paymentmethod import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "method_type",
        "gateway",
        "mno",
        "country_code",
        "currency_code",
        "masked_identifier",
        "is_default",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "method_type",
        "gateway",
        "mno",
        "country_code",
        "currency",
        "is_default",
        "created_at",
    )
    search_fields = (
        "id",
        "owner__username",
        "owner__email",
        "_account_identifier",
    )
    readonly_fields = (
        "account_identifier",
        "metadata",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (_("Basic Info"), {
            "fields": ("owner", "method_type", "gateway", "mno", "country_code", "currency", "is_default")
        }),
        (_("Account Details"), {
            "fields": ("account_identifier", "metadata", "details"),
            "description": _("⚠️ Sensitive fields are encrypted at rest. Values here are auto-decrypted for admin view."),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # ---------------------------
    # Helpers
    # ---------------------------
    def masked_identifier(self, obj):
        """Show last 4 digits only for security"""
        if obj.method_type == "CREDIT_CARD":
            last4 = (obj.details or {}).get("last4")
            return f"****{last4}" if last4 else "-"
        if not obj.account_identifier:
            return "-"
        return f"****{obj.account_identifier[-4:]}"
    masked_identifier.short_description = _("Account")

    def currency_code(self, obj):
        """Show currency code (e.g., TZS)"""
        return obj.currency.code if obj.currency else "-"
    currency_code.short_description = _("Currency")

    def get_queryset(self, request):
        # Optimize performance
        qs = super().get_queryset(request)
        return qs.select_related("owner", "currency")

    # ---------------------------
    # Custom Actions
    # ---------------------------
    actions = ["set_as_default", "export_payment_methods"]

    def set_as_default(self, request, queryset):
        """Mark one payment method as default (others unset)"""
        if queryset.count() != 1:
            self.message_user(request, _("Please select exactly one payment method."), level=messages.ERROR)
            return
        method = queryset.first()
        PaymentMethod.objects.filter(owner=method.owner).update(is_default=False)
        method.is_default = True
        method.save()
        self.message_user(request, _(f"{method} set as default."), level=messages.SUCCESS)
    set_as_default.short_description = _("Set selected method as default")

    def export_payment_methods(self, request, queryset):
        """Export payment methods (sanitized) as CSV"""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="payment_methods.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "ID", "Owner", "Method Type", "Gateway", "MNO",
            "Country", "Currency", "Masked Identifier", "Is Default",
            "Created At", "Updated At"
        ])

        for pm in queryset:
            writer.writerow([
                pm.id,
                pm.owner,
                pm.method_type,
                pm.gateway or "-",
                pm.mno or "-",
                pm.country_code,
                pm.currency.code if pm.currency else "-",
                self.masked_identifier(pm),
                "Yes" if pm.is_default else "No",
                pm.created_at.strftime("%Y-%m-%d %H:%M"),
                pm.updated_at.strftime("%Y-%m-%d %H:%M"),
            ])

        return response
    export_payment_methods.short_description = _("Export selected methods as CSV")