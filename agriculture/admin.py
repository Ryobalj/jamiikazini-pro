from django.contrib import admin

from agriculture.models.harvest_contract import HarvestContract


@admin.register(HarvestContract)
class HarvestContractAdmin(admin.ModelAdmin):
    list_display = ("crop_description", "buyer", "seller", "estimated_weight_kg", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("crop_description",)
    readonly_fields = ("escrow_hold",)
