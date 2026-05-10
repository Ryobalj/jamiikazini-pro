# jamiikazini/syllabus/admins/subject_admin.py

from django.contrib import admin
from syllabus.models.subject import Subject

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "periods_per_week", "description", "created_at")
    search_fields = ("name", "code")
    list_filter = ("created_at", "periods_per_week")
    ordering = ("name",)

    readonly_fields = ("code", "created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "description", "periods_per_week"),
            "description": "Hapa unaweza kuweka idadi ya vipindi kwa wiki kwa kila somo."
        }),
        ("System Generated", {
            "classes": ("collapse",),
            "fields": ("code", "created_at", "updated_at")
        }),
    )