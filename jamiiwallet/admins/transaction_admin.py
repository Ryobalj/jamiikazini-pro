# jamiiwallet/admins/transaction_admin.py

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from jamiiwallet.models.transaction import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'get_reference',
        'transaction_type',
        'wallet',
        'currency_code',
        'amount',
        'status',
        'initiated_by',
        'created_at',
    )
    search_fields = ('idempotency_key', 'wallet__user__email', 'wallet__user__full_name')
    list_filter = ('transaction_type', 'status')
    readonly_fields = ('created_at', 'updated_at', '_reference', 'idempotency_key', 'currency')
    date_hierarchy = 'created_at'
    actions = ['mark_as_completed', 'mark_as_failed']

    def get_reference(self, obj):
        return obj.reference
    get_reference.short_description = "Reference"
    get_reference.admin_order_field = "_reference"

    @admin.action(description="Mark selected transactions as COMPLETED")
    def mark_as_completed(self, request, queryset):
        updated = 0
        for txn in queryset:
            if txn.status != Transaction.TransactionStatus.COMPLETED:
                txn.mark_completed()
                updated += 1
        self.message_user(request, _(f"{updated} transaction(s) marked as COMPLETED."), messages.SUCCESS)

    @admin.action(description="Mark selected transactions as FAILED")
    def mark_as_failed(self, request, queryset):
        updated = 0
        for txn in queryset:
            if txn.status != Transaction.TransactionStatus.FAILED:
                txn.mark_failed()
                updated += 1
        self.message_user(request, _(f"{updated} transaction(s) marked as FAILED."), messages.WARNING)