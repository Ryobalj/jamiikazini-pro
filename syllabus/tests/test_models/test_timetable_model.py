# syllabus/tests/test_models/test_timetable_model.py

import pytest
from django.db.models.signals import post_save
from django.db.utils import IntegrityError
from datetime import time
from jamiiwallet.signals import create_or_reactivate_wallet
from jamiiwallet.models.wallet import Wallet
from payments.models.currency import Currency
from syllabus.models.timetable import TimeTable
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel  # assuming ClassLevel model exists

@pytest.mark.django_db
class TestTimeTableModel:

    @pytest.fixture(autouse=True)
    def disable_wallet_signal(self):
        """
        Disable Wallet post_save signal during these tests to avoid
        duplicate wallet creation errors.
        """
        post_save.disconnect(receiver=create_or_reactivate_wallet, sender=Wallet._meta.get_field('user').remote_field.model)
        yield
        post_save.connect(receiver=create_or_reactivate_wallet, sender=Wallet._meta.get_field('user').remote_field.model)

    @pytest.fixture
    def setup_dependencies(self, user_factory):
        # Create teacher user with role CLIENT
        teacher = user_factory(
            email="teacher1@example.com",
            role="CLIENT",
            full_name="Teacher 1"
        )

        # Ensure default currency exists
        currency, _ = Currency.objects.get_or_create(code="TZS")

        # Create wallet safely
        Wallet.objects.get_or_create(user=teacher, defaults={"currency": currency, "balance": 0.0, "is_active": True})

        # Create workstation
        workstation = TeacherWorkStation.objects.create(
            teacher=teacher,
            school_name="Shule ya Msingi Mzingi",
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

    def test_create_timetable(self, setup_dependencies):
        deps = setup_dependencies
        tt = TimeTable.objects.create(
            workstation=deps["workstation"],
            subject_version=deps["subject_version"],
            period=1,
            timestart=time(8, 0),
            timefinish=time(8, 45),
            registeredboys=20,
            registeredgirls=25,
            status=True,
        )

        assert tt.id is not None
        assert tt.period == 1
        assert tt.registeredboys == 20
        assert tt.registeredgirls == 25
        assert tt.status is True
        assert str(tt) == f"{deps['teacher'].get_full_name()} @ {deps['workstation'].school_name} ({deps['subject_version'].class_level.name}) - Kipindi 1"

    def test_default_values(self, setup_dependencies):
        deps = setup_dependencies
        tt = TimeTable.objects.create(
            workstation=deps["workstation"],
            subject_version=deps["subject_version"],
        )

        assert tt.period == 1
        assert tt.status is False
        assert tt.registeredboys is None
        assert tt.registeredgirls is None

    def test_unique_together_constraint(self, setup_dependencies):
        deps = setup_dependencies

        TimeTable.objects.create(
            workstation=deps["workstation"],
            subject_version=deps["subject_version"],
            period=1,
        )

        with pytest.raises(IntegrityError):
            TimeTable.objects.create(
                workstation=deps["workstation"],
                subject_version=deps["subject_version"],
                period=1,
            )

    def test_multiple_periods_same_workstation_subject_version(self, setup_dependencies):
        deps = setup_dependencies

        tt1 = TimeTable.objects.create(
            workstation=deps["workstation"],
            subject_version=deps["subject_version"],
            period=1,
        )

        tt2 = TimeTable.objects.create(
            workstation=deps["workstation"],
            subject_version=deps["subject_version"],
            period=2,
        )

        assert tt1.period != tt2.period