# logistics/admin/transport_provider_verification_admin.py

from django.contrib import admin
from logistics.models.transport_provider_verification import TransportProviderVerification


@admin.register(TransportProviderVerification)
class TransportProviderVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "institution", "overall_status", "created_at", "updated_at")
    list_filter = ("overall_status", "institution")
    search_fields = ("user__full_name",)
    readonly_fields = ("created_at", "updated_at")