# syllabus/tests/test_serializers/test_class_level_serializer.py

import pytest
from syllabus.models.class_level import ClassLevel
from syllabus.serializers.class_level_serializer import ClassLevelSerializer

@pytest.mark.django_db
class TestClassLevelSerializer:

    def test_name_normalization_and_uniqueness(self):
        ClassLevel.objects.create(name="III")
        serializer = ClassLevelSerializer(data={"name": "iii"})
        assert not serializer.is_valid()
        assert "Darasa hili tayari limesajiliwa." in str(serializer.errors)

    def test_name_is_normalized_to_title_case(self):
        data = {"name": " iv "}
        serializer = ClassLevelSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["name"] == "Iv"

    def test_auto_order_assignment_on_create(self):
        # Initially empty
        serializer = ClassLevelSerializer(data={"name": "V"})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        assert instance.order == 1

        # Add another
        serializer2 = ClassLevelSerializer(data={"name": "VI"})
        serializer2.is_valid(raise_exception=True)
        instance2 = serializer2.save()
        assert instance2.order == 2

    def test_update_preserves_order(self):
        cls = ClassLevel.objects.create(name="VII", order=5)
        serializer = ClassLevelSerializer(cls, data={"name": "vii updated"}, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        assert updated.order == 5
        assert updated.name == "Vii Updated"

    def test_create_sets_order_if_last_order_present(self):
        ClassLevel.objects.create(name="VIII", order=3)
        serializer = ClassLevelSerializer(data={"name": "IX"})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        assert instance.order == 4