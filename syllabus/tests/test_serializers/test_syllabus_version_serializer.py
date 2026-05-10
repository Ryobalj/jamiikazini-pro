# jamiikazini/syllabus/tests/test_serializers/test_syllabus_version_serializer.py

import pytest
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.serializers.syllabus_version_serializer import SyllabusVersionSerializer


@pytest.mark.django_db
class TestSyllabusVersionSerializer:

    def test_create_valid(self):
        data = {
            "year": 2025,
            "evaluation_aid": "Quizzes",
            "is_current": True,
        }
        serializer = SyllabusVersionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()

        assert instance.year == 2025
        assert instance.is_current is True
        assert instance.evaluation_aid == "Quizzes"
        assert serializer.data["display"] == "Syllabus 2025 (current)"

    def test_invalid_year_low(self):
        serializer = SyllabusVersionSerializer(data={"year": 1500})
        assert not serializer.is_valid()
        assert "year" in serializer.errors

    def test_invalid_year_high(self):
        serializer = SyllabusVersionSerializer(data={"year": 2500})
        assert not serializer.is_valid()
        assert "year" in serializer.errors

    def test_model_auto_clears_previous_current_on_create(self):
        old = SyllabusVersion.objects.create(
            year=2023,
            evaluation_aid="Old aids",
            is_current=True,
        )

        data = {
            "year": 2024,
            "evaluation_aid": "New aids",
            "is_current": True,
        }
        serializer = SyllabusVersionSerializer(data=data)
        assert serializer.is_valid()

        new = serializer.save()

        old.refresh_from_db()
        new.refresh_from_db()

        assert new.is_current is True
        assert old.is_current is False  # auto cleared by model.save()

    def test_update_set_current(self):
        old = SyllabusVersion.objects.create(
            year=2023, evaluation_aid="", is_current=True
        )
        target = SyllabusVersion.objects.create(
            year=2025, evaluation_aid="", is_current=False
        )

        serializer = SyllabusVersionSerializer(
            target,
            data={"is_current": True},
            partial=True,
        )
        assert serializer.is_valid()

        updated = serializer.save()

        old.refresh_from_db()
        updated.refresh_from_db()

        assert updated.is_current is True
        assert old.is_current is False  # auto cleared

    def test_display_for_non_current(self):
        inst = SyllabusVersion.objects.create(
            year=2030, evaluation_aid="", is_current=False
        )
        serializer = SyllabusVersionSerializer(inst)

        assert serializer.data["display"] == "Syllabus 2030"

    def test_str_representation(self):
        obj = SyllabusVersion.objects.create(
            year=2040, evaluation_aid="", is_current=True
        )
        assert str(obj) == "Syllabus 2040 (current)"