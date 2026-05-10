# syllabus/tests/test_admin/test_lesson_sentence_admin.py

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
            "teaching_sw_short",
            "teaching_en_short",
            "is_active",
            "created_at",
        )

    def test_list_filter(self, admin_instance):
        assert admin_instance.list_filter == ("category", "is_active")

    def test_search_fields(self, admin_instance):
        assert admin_instance.search_fields == (
            "teaching_sw",
            "teaching_en",
            "reflection_sw",
            "reflection_en",
        )

    def test_ordering(self, admin_instance):
        assert admin_instance.ordering == ("category", "-created_at")

    def test_readonly_fields(self, admin_instance):
        assert admin_instance.readonly_fields == ("created_at", "updated_at")

    def test_fieldsets(self, admin_instance):
        # Extract fieldsets as plain tuples
        fieldsets = tuple((title, opts["fields"]) for title, opts in admin_instance.fieldsets)

        assert fieldsets == (
            ("General", ("category", "is_active")),
            (
                "Swahili Content",
                (
                    "teaching_sw", "learning_sw",
                    "indicator_primary_sw", "indicator_secondary_sw",
                ),
            ),
            (
                "English Content",
                (
                    "teaching_en", "learning_en",
                    "indicator_primary_en", "indicator_secondary_en",
                ),
            ),
            (
                "Reflection / Feedback",
                (
                    "reflection_sw", "reflection_comment_sw",
                    "reflection_en", "reflection_comment_en",
                ),
            ),
            ("Timestamps", ("created_at", "updated_at")),
        )

    def test_teaching_sw_short_method(self, admin_instance):
        obj = LessonSentence(teaching_sw="Hii ni sentensi ya kufundishia kwa Kiswahili ambayo ni ndefu zaidi ya herufi hamsini.")
        result = admin_instance.teaching_sw_short(obj)
        assert result.endswith("...")
        assert len(result) < len(obj.teaching_sw)  # Should be shortened

    def test_teaching_sw_short_empty(self, admin_instance):
        obj = LessonSentence(teaching_sw="")
        assert admin_instance.teaching_sw_short(obj) == ""

    def test_teaching_en_short_method(self, admin_instance):
        obj = LessonSentence(teaching_en="This is an English teaching sentence that exceeds fifty characters long for testing.")
        result = admin_instance.teaching_en_short(obj)
        assert result.endswith("...")
        assert len(result) < len(obj.teaching_en)

    def test_teaching_en_short_empty(self, admin_instance):
        obj = LessonSentence(teaching_en=None)
        assert admin_instance.teaching_en_short(obj) == ""