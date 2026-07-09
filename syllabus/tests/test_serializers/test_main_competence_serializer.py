# syllabus/tests/test_serializers/test_main_competence_serializer.py

import pytest
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.serializers.main_competence_serializer import MainCompetenceSerializer

@pytest.mark.django_db
class TestMainCompetenceSerializer:

    @pytest.fixture
    def syllabus_version(self):
        return SyllabusVersion.objects.create(year=2025)

    @pytest.fixture
    def class_level(self):
        return ClassLevel.objects.create(name="Grade 1", order=1)

    @pytest.fixture
    def subject(self):
        return Subject.objects.create(name="Mathematics")

    @pytest.fixture
    def subject_version(self, syllabus_version, class_level, subject):
        return SubjectVersion.objects.create(
            syllabus_version=syllabus_version,
            class_level=class_level,
            subject=subject
        )

    def test_valid_data_creates_competence(self, subject_version):
        data = {
            "subject_version": subject_version.id,
            "name": "Addition",
        }
        serializer = MainCompetenceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.name == "Addition"
        assert instance.subject_version == subject_version

    def test_empty_name_rejected(self, subject_version):
        data = {"subject_version": subject_version.id, "name": "   "}
        serializer = MainCompetenceSerializer(data=data)
        assert not serializer.is_valid()
        assert ("cannot be empty" in str(serializer.errors)) or ("blank" in str(serializer.errors)) or ("tupu" in str(serializer.errors))

    def test_unique_together_new(self, subject_version):
        MainCompetence.objects.create(subject_version=subject_version, name="Subtraction")
        data = {"subject_version": subject_version.id, "name": "subtraction"}
        serializer = MainCompetenceSerializer(data=data)
        assert not serializer.is_valid()
        assert ("already exists" in str(serializer.errors)) or ("unique" in str(serializer.errors))

    def test_unique_together_update_allow_same_instance(self, subject_version):
        instance = MainCompetence.objects.create(subject_version=subject_version, name="Multiplication")
        data = {"name": "Multiplication"}
        serializer = MainCompetenceSerializer(instance, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.id == instance.id
        assert updated.name == "Multiplication"

    def test_unique_together_update_reject_other(self, subject_version):
        instance1 = MainCompetence.objects.create(subject_version=subject_version, name="Division")
        MainCompetence.objects.create(subject_version=subject_version, name="Fractions")
        data = {"name": "Fractions"}
        serializer = MainCompetenceSerializer(instance1, data=data, partial=True)
        assert not serializer.is_valid()
        assert ("already exists" in str(serializer.errors)) or ("unique" in str(serializer.errors))

    def test_read_only_fields_are_ignored_on_create(self, subject_version):
        data = {
            "subject_version": subject_version.id,
            "name": "Geometry",
            "order": 999,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
        }
        serializer = MainCompetenceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.order != 999  # auto-assigned
        assert instance.name == "Geometry"

    def test_update_works_and_preserves_readonly(self, subject_version):
        instance = MainCompetence.objects.create(subject_version=subject_version, name="Algebra")
        original_order = instance.order
        data = {
            "name": "Advanced Algebra",
            "order": 999,  # should be ignored
        }
        serializer = MainCompetenceSerializer(instance, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.name == "Advanced Algebra"
        assert updated.order == original_order