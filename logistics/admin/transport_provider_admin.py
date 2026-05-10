# logistics/admin/transport_provider_admin.py

from django.contrib import admin
from logistics.models.transport_provider import TransportProvider


@admin.register(TransportProvider)
class TransportProviderAdmin(admin.ModelAdmin):
    list_display = ("user", "provider_type", "institution", "is_approved")
    list_filter = ("provider_type", "is_approved", "institution")
    search_fields = ("user__full_name", "institution__name")
    readonly_fields = ("location",)