# jamiiwallet/admins/wallet_admin.py

from django.contrib import admin
from jamiiwallet.models.wallet import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency', 'is_active', 'last_updated_by', 'updated_at')
    search_fields = ('user__email', 'user__full_name')
    list_filter = ('currency', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'updated_at'