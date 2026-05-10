# logistics/admin/shipment_admin.py

from django.contrib import admin
from logistics.models.shipment import Shipment, ShipmentStatus


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product',
        'sender',
        'receiver',
        'status',
        'tax_paid',
        'transport_fee',
        'jamiikazini_commission',
        'total_cost',
        'created_at',
        'updated_at'
    )
    list_filter = ('status', 'tax_paid', 'created_at')
    search_fields = ('sender__email', 'receiver__email', 'product__name')
    ordering = ('-created_at',)

    autocomplete_fields = ('product', 'sender', 'receiver', 'transport_providers')
    readonly_fields = ('created_at', 'updated_at', 'total_cost')

    fieldsets = (
        ('Shipment Info', {
            'fields': ('product', 'sender', 'receiver', 'preferred_transport_modes', 'route_details')
        }),
        ('Transport & Payment', {
            'fields': ('transport_providers', 'transport_fee', 'jamiikazini_commission', 'total_cost', 'tax_paid')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product', 'sender', 'receiver').prefetch_related('transport_providers')