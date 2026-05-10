# jamiikazini/syllabus/admins/teacher_workstation_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from syllabus.models.teacher_workstation import TeacherWorkStation


@admin.register(TeacherWorkStation)
class TeacherWorkStationAdmin(admin.ModelAdmin):
    """Admin view for managing teacher workstation details."""

    list_display = (
        "teacher",
        "school_name",
        "district",
        "ward",
        "region",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "district",
        "region",
        "created_at",
    )

    search_fields = (
        "teacher__username",
        "teacher__email",
        "school_name",
        "district",
        "ward",
        "region",
    )

    autocomplete_fields = ("teacher",)

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (_("Taarifa za Mwl na Kituo"), {
            "fields": (
                "teacher",
                "school_name",
                "district",
                ("ward", "region"),
            )
        }),
        (_("Hali ya Kazi"), {
            "fields": ("is_active",)
        }),
        (_("Taarifa za Mfumo"), {
            "classes": ("collapse",),
            "fields": ("id", "created_at", "updated_at"),
        }),
    )