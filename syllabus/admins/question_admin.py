# syllabus/admins/question_admin.py

from django.contrib import admin
from syllabus.models.question import Passage, Question


@admin.register(Passage)
class PassageAdmin(admin.ModelAdmin):
    list_display = ("title_preview", "learning_activity", "is_listening", "language")
    list_filter = ("is_listening", "language", "learning_activity__specific_competence__main_competence__subject_version")
    search_fields = ("title", "text", "learning_activity__name")

    def title_preview(self, obj):
        return obj.title or obj.text[:50]
    title_preview.short_description = "Title"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "prompt_preview",
        "question_type",
        "difficulty",
        "learning_activity",
        "marks",
        "is_active",
    )
    list_filter = (
        "question_type",
        "difficulty",
        "is_active",
        "language",
        "learning_activity__specific_competence__main_competence__subject_version__class_level",
        "learning_activity__specific_competence__main_competence__subject_version__subject",
    )
    search_fields = ("prompt", "correct_answer", "source", "learning_activity__name")
    autocomplete_fields = ("learning_activity", "passage")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "learning_activity", "passage"
        )

    def prompt_preview(self, obj):
        return obj.prompt[:60] + ("..." if len(obj.prompt) > 60 else "")
    prompt_preview.short_description = "Prompt"
