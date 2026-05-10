# logistics/admin/driver_admin.py

from django.contrib import admin
from logistics.models.driver import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "license_number", "phone_number", "is_verified", "is_active", "transport_provider")
    list_filter = ("is_verified", "is_active", "transport_provider")
    search_fields = ("full_name", "license_number", "phone_number")