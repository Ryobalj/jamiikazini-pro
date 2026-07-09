# jamiikazini/syllabus/tests/test_admin/test_main_competence_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from syllabus.admins.main_competence_admin import MainCompetenceAdmin
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
from syllabus.models.syllabus_version import SyllabusVersion


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def class_level(db):
    return ClassLevel.objects.create(name="Form 1")


@pytest.fixture
def syllabus_version(db):
    return SyllabusVersion.objects.create(year=2025)


@pytest.fixture
def subject_version(db, subject, class_level, syllabus_version):
    return SubjectVersion.objects.create(
        syllabus_version=syllabus_version,
        subject=subject,
        class_level=class_level
    )


@pytest.fixture
def competence(db, subject_version):
    return MainCompetence.objects.create(
        name="Competence Name Example",
        subject_version=subject_version
    )


@pytest.fixture
def admin_instance():
    return MainCompetenceAdmin(MainCompetence, AdminSite())


def test_list_display(admin_instance):
    assert admin_instance.list_display == (
        "name_preview",
        "subject_version",
        "order",
        "created_at",
        "updated_at"
    )


def test_list_filter(admin_instance):
    assert admin_instance.list_filter == ("subject_version",)


def test_search_fields(admin_instance):
    # Fixed to match new structure: subject_version -> subject
    assert admin_instance.search_fields == ("name", "subject_version__subject__name")


def test_ordering(admin_instance):
    assert admin_instance.ordering == ("subject_version", "order")


def test_readonly_fields(admin_instance):
    assert admin_instance.readonly_fields == ("order", "created_at", "updated_at")


def test_fieldsets_structure(admin_instance):
    fs = admin_instance.fieldsets
    assert fs[0][0] == "General Info"
    # MainCompetence has no is_active field; keep in sync with the admin fieldsets
    assert fs[0][1]["fields"] == ("subject_version", "name", "order")

    assert fs[1][0] == "Timestamps"
    assert fs[1][1]["fields"] == ("created_at", "updated_at")


def test_name_preview_short(admin_instance, competence):
    competence.name = "Short Name"
    assert admin_instance.name_preview(competence) == "Short Name"


def test_name_preview_long(admin_instance, competence):
    long_text = "X" * 70
    competence.name = long_text
    result = admin_instance.name_preview(competence)
    assert result == long_text[:50] + "..."
    assert result.endswith("...")