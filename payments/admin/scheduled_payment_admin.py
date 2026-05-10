# payments/admin/scheduled_payment_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.scheduled_payment import ScheduledPayment

@admin.register(ScheduledPayment)
class ScheduledPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'recipient_user', 'amount', 'currency', 'status', 'schedule_date', 'is_due')
    list_filter = ('status', 'currency', 'schedule_date')
    search_fields = ('created_by__username', 'recipient_user__username', 'description')
    readonly_fields = ('is_due', 'can_be_cancelled', 'created_at', 'updated_at')
    list_select_related = ('created_by', 'recipient_user', 'currency', 'payment_method')

    fieldsets = (
        (_("Taarifa za Msingi"), {
            'fields': ('created_by', 'amount', 'currency', 'payment_method')
        }),
        (_("Mpokeaji"), {
            'fields': ('recipient_user', 'recipient_wallet')
        }),
        (_("Muda na Hali"), {
            'fields': ('schedule_date', 'status', 'is_due', 'can_be_cancelled')
        }),
        (_("Matokeo"), {
            'fields': ('payment_reference', 'executed_at', 'error_message'),
            'classes': ('collapse',)
        }),
        (_("Maelezo"), {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    def is_due(self, obj):
        return obj.is_due
    is_due.boolean = True
    is_due.short_description = _("Imefika Wakati")