from django.contrib import admin
from ..models.staff import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "institution",
        "department",
        "position",
        "phone",
        "is_active",
        "created_at"
    )
    list_filter = ("is_active", "institution", "department")
    search_fields = (
        # "user__first_name",
        "user__full_name",
        "institution__name",
        "department__name",
        "position",
        "phone"
    )
    ordering = ("institution__name", "user__id")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User & Institution", {"fields": ("user", "institution", "department")}),
        ("Details", {"fields": ("title", "position", "phone")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )