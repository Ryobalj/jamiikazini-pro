# jamiikazini/syllabus/admins/class_level_admin.py

from django.contrib import admin
from syllabus.models.class_level import ClassLevel


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order", "description", "created_at", "updated_at")
    list_filter = ("name",)
    search_fields = ("name", "description")
    readonly_fields = ("id", "order", "created_at", "updated_at")
    ordering = ("order",)

    fieldsets = (
        ("Class Level Info", {
            "fields": ("name", "description")
        }),
        ("System Fields", {
            "fields": ("order", "created_at", "updated_at")
        }),
    )