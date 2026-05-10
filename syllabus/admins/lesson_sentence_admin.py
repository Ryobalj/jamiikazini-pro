# jamiikazini/syllabus/admins/lesson_sentence_admin.py

from django.contrib import admin
from syllabus.models.lesson_sentence import LessonSentence

@admin.register(LessonSentence)
class LessonSentenceAdmin(admin.ModelAdmin):
    list_display = (
        "category",
        "short_teaching_sw",
        "short_teaching_en",
        "is_active",
        "is_awali",
        "language",
        "created_at",
    )
    list_filter = ("category", "is_active", "language")
    search_fields = (
        "teaching_sw", "learning_sw", "indicator_primary_sw", "indicator_secondary_sw",
        "teaching_en", "learning_en", "indicator_primary_en", "indicator_secondary_en",
        "reflection_sw", "reflection_en"
    )
    ordering = ("category", "-created_at")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_active",)

    fieldsets = (
        ("General", {"fields": ("category", "language", "is_active")}),
        ("Swahili Content", {
            "fields": (
                "teaching_sw", "learning_sw",
                "indicator_primary_sw", "indicator_secondary_sw"
            ),
            "classes": ("collapse",)
        }),
        ("English Content", {
            "fields": (
                "teaching_en", "learning_en",
                "indicator_primary_en", "indicator_secondary_en"
            ),
            "classes": ("collapse",)
        }),
        ("Reflection / Feedback", {
            "fields": (
                "reflection_sw", "reflection_comment_sw",
                "reflection_en", "reflection_comment_en"
            ),
            "classes": ("collapse",)
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    # ----------------------------------------
    # Helper Methods
    # ----------------------------------------
    def short_text(self, obj, field_name, length=50):
        val = getattr(obj, field_name, "")
        return val[:length] + "..." if val and len(val) > length else val

    def short_teaching_sw(self, obj):
        return self.short_text(obj, "teaching_sw")
    short_teaching_sw.short_description = "Teaching (Sw)"

    def short_teaching_en(self, obj):
        return self.short_text(obj, "teaching_en")
    short_teaching_en.short_description = "Teaching (En)"