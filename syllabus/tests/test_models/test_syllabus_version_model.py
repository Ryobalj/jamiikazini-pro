# jamiikazini/syllabus/tests/test_models/test_syllabus_version_model.py

import pytest
from syllabus.models.syllabus_version import SyllabusVersion
from django.db import IntegrityError


@pytest.mark.django_db
class TestSyllabusVersionModel:

    def test_string_representation(self):
        obj = SyllabusVersion.objects.create(year=2024, is_current=False)
        assert str(obj) == "Syllabus 2024"

    def test_string_representation_current(self):
        obj = SyllabusVersion.objects.create(year=2025, is_current=True)
        assert str(obj) == "Syllabus 2025 (current)"

    def test_unique_year_constraint(self):
        SyllabusVersion.objects.create(year=2024)
        with pytest.raises(IntegrityError):
            SyllabusVersion.objects.create(year=2024)

    def test_only_one_current_syllabus_is_allowed(self):
        # Create an existing current syllabus
        old = SyllabusVersion.objects.create(year=2023, is_current=True)

        # Create new syllabus and set as current
        new = SyllabusVersion.objects.create(year=2024, is_current=True)

        # Refresh from DB
        old.refresh_from_db()
        new.refresh_from_db()

        assert new.is_current is True
        assert old.is_current is False

    def test_save_method_unsets_previous_current(self):
        v1 = SyllabusVersion.objects.create(year=2022, is_current=True)
        v2 = SyllabusVersion.objects.create(year=2023, is_current=True)

        v1.refresh_from_db()
        v2.refresh_from_db()

        assert v2.is_current is True
        assert v1.is_current is False

    def test_meta_ordering(self):
        SyllabusVersion.objects.create(year=2021)
        SyllabusVersion.objects.create(year=2023)
        SyllabusVersion.objects.create(year=2022)

        years = list(SyllabusVersion.objects.values_list("year", flat=True))
        assert years == [2023, 2022, 2021]

    def test_evaluation_aid_is_optional(self):
        obj = SyllabusVersion.objects.create(year=2030)
        assert obj.evaluation_aid == ""