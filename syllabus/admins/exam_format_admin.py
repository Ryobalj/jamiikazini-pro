# syllabus/admins/exam_format_admin.py

import nested_admin
from django.contrib import admin
from syllabus.models.exam_format import ExamFormat, ExamFormatSection, ExamFormatSlot


class ExamFormatSlotInline(nested_admin.NestedTabularInline):
    model = ExamFormatSlot
    extra = 1
    fields = ("order", "question_type", "difficulty", "count", "marks_per_item")


class ExamFormatSectionInline(nested_admin.NestedTabularInline):
    model = ExamFormatSection
    extra = 1
    fields = ("order", "name")
    inlines = [ExamFormatSlotInline]


@admin.register(ExamFormat)
class ExamFormatAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "paper_type", "subject", "class_level", "total_marks", "time_allowed_minutes", "is_active")
    list_filter = ("paper_type", "class_level", "subject", "is_active")
    search_fields = ("name", "subject__name", "class_level__name")
    autocomplete_fields = ("subject", "class_level")
    readonly_fields = ("total_marks",)
    inlines = [ExamFormatSectionInline]

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        form.instance.recompute_total_marks()
