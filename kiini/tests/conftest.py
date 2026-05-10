# conftest.py
import pytest
from django.conf import settings
from kiini.models.institution_type import InstitutionType


@pytest.fixture(autouse=True)
def enable_testing_flag(settings):
    settings.TESTING = True


@pytest.fixture
def institution_type_college(db):
    return InstitutionType.objects.create(
        name=InstitutionType.TypeChoices.COLLEGE,
        description="College"
    )


@pytest.fixture
def institution_type_primary_school(db):
    return InstitutionType.objects.create(
        name=InstitutionType.TypeChoices.PRIMARY_SCHOOL,
        description="Primary School"
    )
