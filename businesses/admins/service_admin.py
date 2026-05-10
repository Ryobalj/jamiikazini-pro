# businesses/admins/service_admin.py

from django.contrib import admin
from businesses.models.service import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'business', 'category', 'price', 'billing_type',
        'location_type', 'requires_booking', 'is_available', 'duration_minutes'
    )
    list_filter = (
        'billing_type', 'location_type', 'requires_booking', 'is_available', 'business', 'category'
    )
    search_fields = ('name', 'business__name', 'category__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('business', 'category', 'name', 'description')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'billing_type', 'location_type', 'requires_booking', 'is_available', 'duration_minutes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )