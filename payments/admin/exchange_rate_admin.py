# payments/admin/exchange_rate_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.exchange_rate import ExchangeRate


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = (
        "base_currency",
        "target_currency",
        "rate",
        "effective_date",
        "source",
        "created",
    )
    list_filter = ("base_currency", "target_currency", "effective_date", "source")
    search_fields = (
        "base_currency__code",
        "target_currency__code",
        "source",
    )
    ordering = ("-effective_date",)
    date_hierarchy = "effective_date"

    fieldsets = (
        (_("Currencies"), {
            "fields": ("base_currency", "target_currency")
        }),
        (_("Rate Information"), {
            "fields": ("rate", "effective_date", "source"),
            "description": _("Weka kiwango cha kubadilisha sarafu ya msingi hadi lengwa.")
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """
        Epuka kufuta viwango vya kubadilisha ili historia ibaki salama.
        Admin anaweza ku-deactivate Currency badala ya kufuta.
        """
        return False