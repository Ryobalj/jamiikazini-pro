# syllabus/tests/test_admin/test_timetable_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from django.db.models.signals import post_save
from datetime import time
from jamiiwallet.signals import create_or_reactivate_wallet
from jamiiwallet.models.wallet import Wallet
from payments.models.currency import Currency
from syllabus.admins.timetable_admin import TimeTableAdmin
from syllabus.models.timetable import TimeTable
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestTimeTableAdmin:

    @pytest.fixture(autouse=True)
    def disable_wallet_signal(self):
        """Disable Wallet post_save signal during these tests."""
        post_save.disconnect(receiver=create_or_reactivate_wallet, sender=Wallet._meta.get_field('user').remote_field.model)
        yield
        post_save.connect(receiver=create_or_reactivate_wallet, sender=Wallet._meta.get_field('user').remote_field.model)

    @pytest.fixture
    def setup_dependencies(self, user_factory):
        # Create teacher user with role CLIENT
        teacher = user_factory(
            email="teacher1@example.com",
            role="CLIENT",
            full_name="Teacher One"
        )

        # Ensure default currency exists
        currency, _ = Currency.objects.get_or_create(code="TZS")

        # Create wallet safely
        Wallet.objects.get_or_create(user=teacher, defaults={"currency": currency, "balance": 0.0, "is_active": True})

        # Create workstation
        workstation = TeacherWorkStation.objects.create(
            teacher=teacher,
            school_name="Alpha School",
            district="Mkinga",
        )

        # Create class level
        class_level = ClassLevel.objects.create(name="Form 1")

        # Create syllabus version
        syllabus_version = SyllabusVersion.objects.create(year=2025)

        # Create subject
        subject = Subject.objects.create(name="Mathematics")

        # Create subject version
        subject_version = SubjectVersion.objects.create(
            syllabus_version=syllabus_version,
            subject=subject,
            class_level=class_level,
        )

        return {
            "teacher": teacher,
            "workstation": workstation,
            "class_level": class_level,
            "syllabus_version": syllabus_version,
            "subject": subject,
            "subject_version": subject_version,
        }

    @pytest.fixture
    def timetable(self, setup_dependencies):
        deps = setup_dependencies
        return TimeTable.objects.create(
            workstation=deps["workstation"],
            subject_version=deps["subject_version"],
            period=1,
        )

    @pytest.fixture
    def admin_site(self):
        return AdminSite()

    def test_workstation_display(self, timetable, admin_site):
        admin = TimeTableAdmin(TimeTable, admin_site)
        display = admin.workstation_display(timetable)
        assert display == f"{timetable.workstation.teacher.get_full_name()} — {timetable.workstation.school_name}"

    def test_subject_display(self, timetable, admin_site):
        admin = TimeTableAdmin(TimeTable, admin_site)
        sv = timetable.subject_version
        display = admin.subject_display(timetable)
        assert display == f"{sv.subject.name} ({sv.class_level.name})"

    def test_list_display_fields(self, admin_site):
        admin = TimeTableAdmin(TimeTable, admin_site)
        assert "workstation_display" in admin.list_display
        assert "subject_display" in admin.list_display
        assert "period" in admin.list_display

    def test_readonly_fields(self, admin_site):
        admin = TimeTableAdmin(TimeTable, admin_site)
        assert "created_at" in admin.readonly_fields
        assert "updated_at" in admin.readonly_fields

    def test_get_queryset_select_related(self, admin_site, timetable):
        admin = TimeTableAdmin(TimeTable, admin_site)
        qs = admin.get_queryset(request=None)
        sql = str(qs.query)
        assert "JOIN" in sql or "SELECT" in sql