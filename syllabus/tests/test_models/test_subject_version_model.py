# jamiikazini/syllabus/tests/test_models/test_subject_version_model.py

import pytest
from django.db import IntegrityError
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.class_level import ClassLevel


@pytest.mark.django_db
class TestSubjectVersionModel:

    def setup_method(self):
        self.syllabus_v1 = SyllabusVersion.objects.create(year=2024)
        self.syllabus_v2 = SyllabusVersion.objects.create(year=2025)

        self.subject_math = Subject.objects.create(name="Mathematics")
        self.subject_eng = Subject.objects.create(name="English")

        self.level_p1 = ClassLevel.objects.create(name="P1", order=1)
        self.level_p2 = ClassLevel.objects.create(name="P2", order=2)

    def test_auto_order_increment(self):
        v1 = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_math,
            class_level=self.level_p1
        )
        v2 = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_eng,
            class_level=self.level_p1
        )

        assert v1.order == 1
        assert v2.order == 2

    def test_auto_order_respects_syllabus_and_class_level(self):
        """
        Should reset ordering when class level or syllabus version changes
        """
        v1 = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_math,
            class_level=self.level_p1
        )
        v2 = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_eng,
            class_level=self.level_p2
        )

        assert v1.order == 1
        assert v2.order == 1  # resets for new class level

    def test_unique_together_constraint(self):
        SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_math,
            class_level=self.level_p1
        )

        with pytest.raises(IntegrityError):
            SubjectVersion.objects.create(
                syllabus_version=self.syllabus_v1,
                subject=self.subject_math,
                class_level=self.level_p1
            )

    def test_boolean_fields_default(self):
        v = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_math,
            class_level=self.level_p1
        )

        assert v.is_english is False
        assert v.is_awali is False

    def test_boolean_flags_can_be_set(self):
        v = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v2,
            subject=self.subject_eng,
            class_level=self.level_p2,
            is_english=True,
            is_awali=True
        )

        assert v.is_english is True
        assert v.is_awali is True

    def test_str_representation(self):
        v = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_math,
            class_level=self.level_p1
        )

        expected = "Mathematics (P1) - 2024"
        assert str(v) == expected

    def test_model_ordering(self):
        """
        Ordering: ["syllabus_version", "class_level", "order"]
        """
        v1 = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v1,
            subject=self.subject_math,
            class_level=self.level_p1
        )
        v2 = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_v2,
            subject=self.subject_math,
            class_level=self.level_p1
        )

        # must use order_by() for reliable ordering inside pytest

        all_items = list(
            SubjectVersion.objects.order_by(
                "syllabus_version__year",
                "class_level__order",
                "order",
            )
        )

        assert all_items == [v1, v2]