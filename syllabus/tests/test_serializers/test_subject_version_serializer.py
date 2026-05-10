# jamiikazini/syllabus/tests/test_serializers/test_subject_version_serializer.py

import pytest
from rest_framework.exceptions import ValidationError
from syllabus.serializers.subject_version_serializer import SubjectVersionSerializer
from syllabus.models import SubjectVersion, SyllabusVersion, Subject, ClassLevel


@pytest.mark.django_db
class TestSubjectVersionSerializer:

    # ------------------------------------------------
    # FACTORY HELPERS
    # ------------------------------------------------
    @pytest.fixture
    def syllabus_version(self):
        return SyllabusVersion.objects.create(year=2024)

    @pytest.fixture
    def subject(self):
        return Subject.objects.create(name="Mathematics")

    @pytest.fixture
    def class_level(self):
        return ClassLevel.objects.create(name="Grade 3", order=1)

    @pytest.fixture
    def subject_version(self, syllabus_version, subject, class_level):
        return SubjectVersion.objects.create(
            syllabus_version=syllabus_version,
            subject=subject,
            class_level=class_level,
            is_english=True,
            is_awali=False,
        )

    # ------------------------------------------------
    # BOOLEAN VALIDATION TESTS
    # ------------------------------------------------
    def test_boolean_fields_validation(self, syllabus_version, subject, class_level):
        data = {
            "syllabus_version": syllabus_version.id,
            "subject": subject.id,
            "class_level": class_level.id,
            "is_english": "invalid",
            "is_awali": False,
        }

        serializer = SubjectVersionSerializer(data=data)
        assert not serializer.is_valid()
        assert "is_english" in serializer.errors

    # ------------------------------------------------
    # UNIQUE COMBINATION TEST
    # ------------------------------------------------
    def test_unique_combination_validation(
        self, syllabus_version, subject, class_level, subject_version
    ):
        data = {
            "syllabus_version": syllabus_version.id,
            "subject": subject.id,
            "class_level": class_level.id,
            "is_english": False,
            "is_awali": False,
        }

        serializer = SubjectVersionSerializer(data=data)
        assert not serializer.is_valid()
        assert "class_level" in serializer.errors
        assert (
            serializer.errors["class_level"][0]
            == "This combination of syllabus_version, subject and class_level already exists."
        )

    # ------------------------------------------------
    # ALLOW UPDATE IF SAME RECORD
    # ------------------------------------------------
    def test_update_allows_same_unique_combination(self, subject_version):
        data = {
            "syllabus_version": subject_version.syllabus_version.id,
            "subject": subject_version.subject.id,
            "class_level": subject_version.class_level.id,
            "is_english": True,
            "is_awali": False,
        }

        serializer = SubjectVersionSerializer(
            instance=subject_version,
            data=data,
            partial=True,
        )

        assert serializer.is_valid()

    # ------------------------------------------------
    # TEST CREATE SUCCESSFUL
    # ------------------------------------------------
    def test_create_success(self, syllabus_version, subject, class_level):
        data = {
            "syllabus_version": syllabus_version.id,
            "subject": subject.id,
            "class_level": class_level.id,
            "is_english": True,
            "is_awali": True,
        }

        serializer = SubjectVersionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.id is not None
        assert instance.order == 1  # auto order

    # ------------------------------------------------
    # TEST READ-ONLY FIELDS
    # ------------------------------------------------
    def test_read_only_fields(self, syllabus_version, subject, class_level):
        data = {
            "syllabus_version": syllabus_version.id,
            "subject": subject.id,
            "class_level": class_level.id,
            "is_english": True,
            "is_awali": True,
            "order": 999,  # ignored
        }

        serializer = SubjectVersionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()

        assert instance.order == 1  # still auto generated, not 999