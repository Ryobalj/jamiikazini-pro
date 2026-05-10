# payments/admin/bulk_payment_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.bulk_payment import BulkPaymentTemplate, BulkPaymentExecution

@admin.register(BulkPaymentTemplate)
class BulkPaymentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'total_payments', 'total_amount', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'created_by__username')
    readonly_fields = ('total_payments', 'total_amount', 'created_at', 'updated_at')
    list_select_related = ('created_by',)

    fieldsets = (
        (_("Taarifa za Msingi"), {
            'fields': ('created_by', 'name', 'description', 'is_active')
        }),
        (_("Data ya Malipo"), {
            'fields': ('payments_data', 'metadata'),
            'classes': ('collapse',)
        }),
        (_("Takwimu"), {
            'fields': ('total_payments', 'total_amount'),
            'classes': ('collapse',)
        }),
        (_("Muda"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BulkPaymentExecution)
class BulkPaymentExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'executed_by', 'template', 'status', 'successful_count', 'failed_count', 'executed_at')
    list_filter = ('status', 'executed_at')
    search_fields = ('executed_by__username', 'template__name')
    readonly_fields = ('success_rate', 'is_completed', 'executed_at', 'completed_at')
    list_select_related = ('executed_by', 'template')

    fieldsets = (
        (_("Taarifa za Utekelezaji"), {
            'fields': ('executed_by', 'template', 'status', 'idempotency_key')
        }),
        (_("Matokeo"), {
            'fields': ('total_payments', 'successful_count', 'failed_count', 'success_rate', 'results')
        }),
        (_("Muda"), {
            'fields': ('executed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def success_rate(self, obj):
        return f"{obj.success_rate:.1f}%"
    success_rate.short_description = _("Kiwango cha Mafanikio")