# syllabus/tests/test_serializers/test_lesson_sentence_serializer.py

import pytest
from syllabus.serializers.lesson_sentence_serializer import LessonSentenceSerializer
from syllabus.models.lesson_sentence import LessonSentence


@pytest.mark.django_db
class TestLessonSentenceSerializer:

    def valid_payload(self):
        """Helper to generate valid data"""
        return {
            "category": LessonSentence.Category.INTRO,
            "teaching_sw": "   Kuwahoji wanafunzi juu ya mada   ",
            "learning_sw": "   Kujibu maswali   ",
            "indicator_primary_sw": "   Indicator   ",
            "indicator_secondary_sw": "   Secondary   ",
            "teaching_en": "",
            "learning_en": "",
            "indicator_primary_en": "",
            "indicator_secondary_en": "",
            "reflection_sw": "   Reflect sw   ",
            "reflection_comment_sw": "   Comment sw   ",
            "reflection_en": "",
            "reflection_comment_en": "",
            "is_active": True,
        }

    # --------------------------------------------------
    # CATEGORY VALIDATION
    # --------------------------------------------------
    def test_invalid_category(self):
        data = self.valid_payload()
        data["category"] = "wrong_value"

        serializer = LessonSentenceSerializer(data=data)

        assert not serializer.is_valid()
        assert "category" in serializer.errors

    def test_missing_category(self):
        data = self.valid_payload()
        data["category"] = None

        serializer = LessonSentenceSerializer(data=data)

        assert not serializer.is_valid()
        assert "category" in serializer.errors

    # --------------------------------------------------
    # TEACHING CONTENT VALIDATION
    # --------------------------------------------------
    def test_requires_at_least_one_teaching_field(self):
        data = self.valid_payload()
        data["teaching_sw"] = "   "
        data["teaching_en"] = "   "

        serializer = LessonSentenceSerializer(data=data)

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    # --------------------------------------------------
    # TRIM LOGIC CHECK
    # --------------------------------------------------
    def test_trims_text_fields(self):
        data = self.valid_payload()

        serializer = LessonSentenceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()

        assert instance.teaching_sw == "Kuwahoji wanafunzi juu ya mada"
        assert instance.learning_sw == "Kujibu maswali"
        assert instance.indicator_primary_sw == "Indicator"
        assert instance.indicator_secondary_sw == "Secondary"
        assert instance.reflection_sw == "Reflect sw"
        assert instance.reflection_comment_sw == "Comment sw"

    # --------------------------------------------------
    # SUCCESSFUL CREATE
    # --------------------------------------------------
    def test_create_success(self):
        data = self.valid_payload()

        serializer = LessonSentenceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()

        assert isinstance(obj, LessonSentence)
        assert obj.category == LessonSentence.Category.INTRO
        assert obj.is_active is True

    # --------------------------------------------------
    # UPDATE PRESERVES DATA AND TRIMS
    # --------------------------------------------------
    def test_update_serializer(self):
        # create instance
        instance = LessonSentence.objects.create(
            category=LessonSentence.Category.DEVELOPMENT,
            teaching_sw="Initial",
        )

        data = {
            "teaching_sw": "   Updated teaching   ",
            "teaching_en": ""
        }

        serializer = LessonSentenceSerializer(
            instance, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.teaching_sw == "Updated teaching"
        assert updated.category == LessonSentence.Category.DEVELOPMENT  # unchanged