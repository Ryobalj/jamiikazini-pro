from django.contrib import admin

from billpay.models.biller import Biller
from billpay.models.bill_payment import BillPayment


@admin.register(Biller)
class BillerAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "country", "config_key", "is_active")
    list_filter = ("category", "country", "is_active")
    search_fields = ("name", "config_key")


@admin.register(BillPayment)
class BillPaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "biller", "account_number", "amount", "status", "created_at")
    list_filter = ("status", "biller")
    search_fields = ("account_number", "external_reference")
    readonly_fields = ("wallet_transaction", "response_data", "created_at", "updated_at")
