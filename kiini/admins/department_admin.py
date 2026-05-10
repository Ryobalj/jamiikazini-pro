from django.contrib import admin
from ..models.department import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "institution", "is_active", "created_at")
    list_filter = ("is_active", "institution")
    search_fields = ("name", "institution__name")
    list_editable = ("is_active",)
    ordering = ("institution__name", "name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("institution", "name", "description")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )