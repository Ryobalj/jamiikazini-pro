# syllabus/tests/test_admin/test_lesson_sentence_admin.py
# Imefuatishwa na LessonSentenceAdmin ya sasa (short_teaching_sw/short_teaching_en,
# language kwenye list_display/filters/fieldsets, search_fields kamili).

import pytest
from django.contrib import admin
from syllabus.models.lesson_sentence import LessonSentence
from syllabus.admins.lesson_sentence_admin import LessonSentenceAdmin


@pytest.mark.django_db
class TestLessonSentenceAdmin:

    @pytest.fixture
    def admin_instance(self):
        return LessonSentenceAdmin(model=LessonSentence, admin_site=admin.site)

    def test_list_display(self, admin_instance):
        assert admin_instance.list_display == (
            "category",
            "short_teaching_sw",
            "short_teaching_en",
            "is_active",
            "is_awali",
            "language",
            "created_at",
        )

    def test_list_filter(self, admin_instance):
        assert admin_instance.list_filter == ("category", "is_active", "language")

    def test_search_fields(self, admin_instance):
        assert "teaching_sw" in admin_instance.search_fields
        assert "teaching_en" in admin_instance.search_fields
        assert "reflection_sw" in admin_instance.search_fields
        assert "reflection_en" in admin_instance.search_fields

    def test_ordering(self, admin_instance):
        assert admin_instance.ordering == ("category", "-created_at")

    def test_readonly_fields(self, admin_instance):
        assert admin_instance.readonly_fields == ("created_at", "updated_at")

    def test_fieldsets(self, admin_instance):
        titles = [title for title, _ in admin_instance.fieldsets]
        assert titles == [
            "General", "Swahili Content", "English Content",
            "Reflection / Feedback", "Timestamps",
        ]
        general_fields = dict(admin_instance.fieldsets)["General"]["fields"]
        assert general_fields == ("category", "language", "is_active")

    def test_short_teaching_sw_method(self, admin_instance):
        obj = LessonSentence(teaching_sw="Hii ni sentensi ya kufundishia kwa Kiswahili ambayo ni ndefu zaidi ya herufi hamsini.")
        result = admin_instance.short_teaching_sw(obj)
        assert result.endswith("...")
        assert len(result) < len(obj.teaching_sw)

    def test_short_teaching_sw_empty(self, admin_instance):
        obj = LessonSentence(teaching_sw="")
        assert admin_instance.short_teaching_sw(obj) == ""

    def test_short_teaching_en_method(self, admin_instance):
        obj = LessonSentence(teaching_en="This is an English teaching sentence that exceeds fifty characters long for testing.")
        result = admin_instance.short_teaching_en(obj)
        assert result.endswith("...")
        assert len(result) < len(obj.teaching_en)

    def test_short_teaching_en_empty(self, admin_instance):
        obj = LessonSentence(teaching_en="")
        assert admin_instance.short_teaching_en(obj) == ""
