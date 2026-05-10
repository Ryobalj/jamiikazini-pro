# kiini/admins/institution_type_admin.py

from django.contrib import admin
from kiini.models.institution_type import InstitutionType


@admin.register(InstitutionType)
class InstitutionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "get_name_display", "description", "created_at", "updated_at")
    list_filter = ("name",)
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("name", "description")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = "Display Name"