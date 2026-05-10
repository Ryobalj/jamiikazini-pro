# payments/admin/payment_link_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.payment_link import PaymentLink

@admin.register(PaymentLink)
class PaymentLinkAdmin(admin.ModelAdmin):
    list_display = ('link_code', 'created_by', 'amount', 'currency', 'status', 'is_usable', 'expires_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('link_code', 'created_by__username', 'description')
    readonly_fields = ('is_usable', 'is_expired', 'get_absolute_url', 'created_at', 'updated_at')
    list_select_related = ('created_by', 'currency')

    fieldsets = (
        (_("Taarifa za Kiungo"), {
            'fields': ('created_by', 'amount', 'currency', 'description', 'link_code')
        }),
        (_("Muda na Hali"), {
            'fields': ('expires_at', 'status', 'is_usable', 'is_expired')
        }),
        (_("Matumizi"), {
            'fields': ('used_by', 'used_at', 'payment_reference'),
            'classes': ('collapse',)
        }),
        (_("Mipangilio"), {
            'fields': ('allowed_methods', 'metadata'),
            'classes': ('collapse',)
        }),
        (_("Kiungo"), {
            'fields': ('get_absolute_url',),
            'classes': ('collapse',)
        }),
    )

    def is_usable(self, obj):
        return obj.is_usable
    is_usable.boolean = True
    is_usable.short_description = _("Inaweza Kutumika")