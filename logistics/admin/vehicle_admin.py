from django.contrib import admin
from logistics.models.vehicle import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'registration_number',
        'vehicle_type',
        'provider',
        'capacity_kg',
        'volume_cbm',
        'is_active',
        'active_driver',
        'created_at',
    )
    list_filter = ('vehicle_type', 'is_active', 'provider')
    search_fields = ('registration_number', 'model_name', 'provider__name')
    autocomplete_fields = ('provider', 'drivers', 'active_driver')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': (
                'provider',
                'vehicle_type',
                'registration_number',
                'model_name',
                'capacity_kg',
                'volume_cbm',
                'image',
                'is_active',
            )
        }),
        ('Drivers & Status', {
            'fields': (
                'drivers',
                'active_driver',
                'verification_statuses',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )