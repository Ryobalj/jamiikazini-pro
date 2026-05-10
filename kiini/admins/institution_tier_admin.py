# kiini/admin/institution_tier_admin.py

from django.contrib import admin
from kiini.models.institution_tier import InstitutionTier

@admin.register(InstitutionTier)
class InstitutionTierAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")