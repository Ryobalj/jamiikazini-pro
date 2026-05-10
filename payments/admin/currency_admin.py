# payments/admin/currency_admin.py 

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.currency import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "country", "exchange_rate_to_tzs", "is_active")
    list_filter = ("is_active", "country")
    search_fields = ("code", "name", "country")
    ordering = ("code",)
    list_editable = ("exchange_rate_to_tzs", "is_active")
    readonly_fields = ("name", "symbol")  # Zinawekwa auto kwenye save()

    fieldsets = (
        (_("Currency Information"), {
            "fields": ("code", "name", "symbol", "country", "is_active")
        }),
        (_("Exchange Rate"), {
            "fields": ("exchange_rate_to_tzs",),
            "description": _("Kiwango cha kubadilisha fedha hii kulinganisha na Tanzanian Shilling (TZS).")
        }),
    )

    def get_queryset(self, request):
        """Improve performance kwa prefetch / select related ikiwa inahitajika."""
        return super().get_queryset(request)

    def has_delete_permission(self, request, obj=None):
        """
        Epuka kufuta currency kwa bahati mbaya.
        Badala yake, admin anaweza ku-deactivate tu.
        """
        return False
