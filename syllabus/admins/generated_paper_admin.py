# syllabus/admins/generated_paper_admin.py

from django.contrib import admin
from syllabus.models.generated_paper import GeneratedPaper, GeneratedPaperQuestion


class GeneratedPaperQuestionInline(admin.TabularInline):
    model = GeneratedPaperQuestion
    extra = 0
    fields = ("section_name", "order_in_section", "question", "marks")
    readonly_fields = ("section_name", "order_in_section", "question", "marks")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(GeneratedPaper)
class GeneratedPaperAdmin(admin.ModelAdmin):
    list_display = ("title_or_format", "subject_version", "workstation", "exam_format", "year", "term", "created_at")
    list_filter = ("exam_format__paper_type", "subject_version__class_level", "year", "term")
    search_fields = ("title", "workstation__school_name", "subject_version__subject__name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "exam_format", "subject_version", "workstation"
        )

    def title_or_format(self, obj):
        return obj.title or obj.exam_format.name
    title_or_format.short_description = "Title"

    inlines = [GeneratedPaperQuestionInline]
