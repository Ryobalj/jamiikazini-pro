# jamiikazini/syllabus/tests/test_serializers/test_subject_serializer.py

import pytest
from syllabus.models.subject import Subject
from syllabus.serializers.subject_serializer import SubjectSerializer


@pytest.mark.django_db
class TestSubjectSerializer:

    def test_serializer_fields(self):
        serializer = SubjectSerializer()
        expected_fields = {
            "id",
            "name",
            "code",
            "description",
            "periods_per_week",
            "created_at",
            "updated_at",
            "display",
        }
        assert set(serializer.fields.keys()) == expected_fields

    def test_validate_name_unique_case_insensitive(self):
        Subject.objects.create(name="Biology")
        data = {"name": "biology"}

        serializer = SubjectSerializer(data=data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"][0] == "Subject with this name already exists."

    def test_validate_name_allows_update_if_same_name(self):
        subject = Subject.objects.create(name="Chemistry")

        serializer = SubjectSerializer(
            instance=subject,
            data={"name": "Chemistry", "description": "Updated"}
        )

        assert serializer.is_valid()

    def test_read_only_code_not_overwritten(self):
        """
        Ensure user cannot override auto-generated code
        """
        subject = Subject.objects.create(name="Physics")
        previous_code = subject.code

        serializer = SubjectSerializer(
            instance=subject,
            data={"name": "Physics", "code": "FAKE123"},
            partial=True
        )
        assert serializer.is_valid()
        result = serializer.save()

        assert result.code == previous_code

    def test_representation_includes_display(self):
        subject = Subject.objects.create(name="Civics")
        serializer = SubjectSerializer(subject)
        rep = serializer.data

        assert "display" in rep
        assert rep["display"] == f"{subject.name} ({subject.code})"