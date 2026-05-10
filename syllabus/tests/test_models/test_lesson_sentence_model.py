# syllabus/tests/test_models/test_lesson_sentence_model.py

import pytest
from syllabus.models.lesson_sentence import LessonSentence


@pytest.mark.django_db
class TestLessonSentenceModel:

    @pytest.fixture
    def sample_sentence(self):
        return LessonSentence.objects.create(
            category=LessonSentence.Category.INTRO,
            teaching_sw="Kuwahoji wanafunzi juu ya mada fulani.",
        )

    def test_str_method(self, sample_sentence):
        result = str(sample_sentence)
        assert "Utangulizi" in result  # get_category_display()
        assert "Kuwahoji wanafunzi"[:30] in result

    def test_defaults(self):
        obj = LessonSentence.objects.create()
        assert obj.is_active is True
        assert obj.teaching_sw == ""
        assert obj.learning_sw == ""
        assert obj.teaching_en == ""
        assert obj.learning_en == ""
        assert obj.reflection_sw == ""
        assert obj.reflection_comment_sw == ""
        assert obj.reflection_en == ""
        assert obj.reflection_comment_en == ""

    def test_category_choices(self, sample_sentence):
        assert sample_sentence.category == "intro"
        assert sample_sentence.get_category_display().startswith("Utangulizi")

    def test_meta_ordering(self):
        meta = LessonSentence._meta
        assert meta.ordering == ["category", "-created_at"]

    # --- pick_random tests ---

    def test_pick_random_returns_object(self):
        s1 = LessonSentence.objects.create(
            category=LessonSentence.Category.INTRO,
            teaching_sw="A",
        )
        s2 = LessonSentence.objects.create(
            category=LessonSentence.Category.INTRO,
            teaching_sw="B",
        )

        result = LessonSentence.pick_random(LessonSentence.Category.INTRO)
        assert result is not None
        assert result.category == LessonSentence.Category.INTRO
        assert isinstance(result, LessonSentence)

    def test_pick_random_returns_none_when_empty(self):
        result = LessonSentence.pick_random(LessonSentence.Category.CONCLUSION)
        assert result is None

    def test_pick_random_only_active(self):
        active = LessonSentence.objects.create(
            category=LessonSentence.Category.DEVELOPMENT,
            teaching_sw="Active sentence",
            is_active=True,
        )
        inactive = LessonSentence.objects.create(
            category=LessonSentence.Category.DEVELOPMENT,
            teaching_sw="Inactive",
            is_active=False,
        )

        result = LessonSentence.pick_random(LessonSentence.Category.DEVELOPMENT)

        # Lazima apewe active tu
        assert result.is_active is True
        assert result.teaching_sw == active.teaching_sw

    def test_pick_random_multiple_active(self):
        """Ensure selection among actives only."""
        active1 = LessonSentence.objects.create(
            category=LessonSentence.Category.REFLECTION,
            teaching_sw="A",
            is_active=True,
        )
        active2 = LessonSentence.objects.create(
            category=LessonSentence.Category.REFLECTION,
            teaching_sw="B",
            is_active=True,
        )
        inactive = LessonSentence.objects.create(
            category=LessonSentence.Category.REFLECTION,
            teaching_sw="C",
            is_active=False,
        )

        # Collect many picks to ensure only active results come out
        results = {
            LessonSentence.pick_random(LessonSentence.Category.REFLECTION).teaching_sw
            for _ in range(20)
        }

        assert "C" not in results  # inactive never selected
        assert results.issubset({"A", "B"})
        assert len(results) >= 1