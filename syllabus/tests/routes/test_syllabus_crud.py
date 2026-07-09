# syllabus/tests/test_syllabus_crud.py

import pytest
import uuid
from accounts.models import User
from syllabus.models.subject import Subject
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.class_level import ClassLevel
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.timetable import TimeTable
from django.db.models import signals
from jamiiwallet.models.wallet import Wallet
from rest_framework.test import APIClient

BASE_URL = "/api/v1/syllabus/"

# ==========================================
# Disable Wallet Signal Module-Level
# ==========================================
@pytest.fixture(autouse=True)
def disable_wallet_signal():
    """Disable wallet auto-create signal for all tests."""
    try:
        signals.post_save.disconnect(Wallet.create_wallet_for_user, sender=User)
    except Exception:
        pass

# ==========================================
# Test Class
# ==========================================
@pytest.mark.django_db(transaction=True)
class TestSyllabusCRUD:

    @pytest.fixture(autouse=True)
    def setup(self, user_factory, api_client):
        # Admin user for all endpoints
        self.admin = user_factory(role="ADMIN")
        self.client = api_client
        self.client.force_authenticate(self.admin)

        # Common objects
        self.class_level = ClassLevel.objects.create(
            name=f"Grade 1 {uuid.uuid4().hex[:6]}", order=1
        )
        self.syllabus_version = SyllabusVersion.objects.create(
            year=2025, is_current=True
        )

    # -------------------------
    # Subject CRUD (Admin only)
    # -------------------------
    def test_subject_crud(self):
        name = f"Math {uuid.uuid4().hex[:6]}"
        payload = {"name": name, "periods_per_week": 5}
        resp = self.client.post(f"{BASE_URL}subjects/", payload)
        assert resp.status_code == 201
        subj_id = resp.json()["id"]

        resp2 = self.client.get(f"{BASE_URL}subjects/{subj_id}/")
        assert resp2.status_code == 200
        # Serializer hufanya .title() kwenye jina - linganisha bila kujali herufi
        assert resp2.json()["name"].lower() == name.lower()

        resp3 = self.client.patch(f"{BASE_URL}subjects/{subj_id}/", {"periods_per_week": 6})
        assert resp3.status_code == 200
        assert resp3.json()["periods_per_week"] == 6

        resp4 = self.client.delete(f"{BASE_URL}subjects/{subj_id}/")
        assert resp4.status_code == 204

    # -------------------------
    # Syllabus Version CRUD (Admin only)
    # -------------------------
    def test_syllabus_version_crud(self):
        year = 2030
        payload = {"year": year}
        resp = self.client.post(f"{BASE_URL}syllabus-versions/", payload)
        assert resp.status_code == 201
        sv_id = resp.json()["id"]

        resp2 = self.client.get(f"{BASE_URL}syllabus-versions/{sv_id}/")
        assert resp2.status_code == 200
        assert resp2.json()["year"] == year

        resp3 = self.client.patch(f"{BASE_URL}syllabus-versions/{sv_id}/", {"is_current": True})
        assert resp3.status_code == 200

        resp4 = self.client.delete(f"{BASE_URL}syllabus-versions/{sv_id}/")
        assert resp4.status_code == 204

    # -------------------------
    # SubjectVersion CRUD (Admin only)
    # -------------------------
    def test_subject_version_crud(self):
        subj = Subject.objects.create(
            name=f"Science {uuid.uuid4().hex[:6]}", periods_per_week=5
        )
        payload = {
            "syllabus_version": self.syllabus_version.id,
            "subject": subj.id,
            "class_level": self.class_level.id,
            "is_english": True,
            "is_awali": False
        }
        resp = self.client.post(f"{BASE_URL}subject-versions/", payload)
        assert resp.status_code == 201
        sv_id = resp.json()["id"]

        resp2 = self.client.get(f"{BASE_URL}subject-versions/{sv_id}/")
        assert resp2.status_code == 200

        resp3 = self.client.patch(f"{BASE_URL}subject-versions/{sv_id}/", {"is_awali": True})
        assert resp3.status_code == 200

        resp4 = self.client.delete(f"{BASE_URL}subject-versions/{sv_id}/")
        assert resp4.status_code == 204

    # -------------------------
    # TeacherWorkStation CRUD (Admin)
    # -------------------------
    def test_teacher_workstation_crud(self):
        payload = {
            "teacher": self.admin.id,
            "school_name": f"Test School {uuid.uuid4().hex[:6]}",
            "district": "District A",
            "ward": "Ward B",
            "region": "Region C",
            "is_active": True
        }
        resp = self.client.post(f"{BASE_URL}teacher-workstations/", payload)
        assert resp.status_code == 201
        ws_id = resp.json()["id"]

        resp2 = self.client.get(f"{BASE_URL}teacher-workstations/{ws_id}/")
        assert resp2.status_code == 200

        resp3 = self.client.patch(f"{BASE_URL}teacher-workstations/{ws_id}/", {"is_active": False})
        assert resp3.status_code == 200

        resp4 = self.client.delete(f"{BASE_URL}teacher-workstations/{ws_id}/")
        assert resp4.status_code == 204

    # -------------------------
    # TimeTable CRUD (Admin)
    # -------------------------
    def test_timetable_crud(self):
        subject = Subject.objects.create(name=f"English {uuid.uuid4().hex[:6]}", periods_per_week=5)
        subj_version = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_version,
            subject=subject,
            class_level=self.class_level,
            is_english=True,
            is_awali=False
        )
        ws = TeacherWorkStation.objects.create(
            teacher=self.admin,
            school_name=f"School {uuid.uuid4().hex[:6]}",
            district="District 1",
            ward="Ward 1",
            region="Region 1",
            is_active=True
        )
        payload = {
            "workstation": ws.id,
            "subject_version": subj_version.id,
            "period": 1,
            "timestart": "08:00:00",
            "timefinish": "09:00:00",
            "registeredboys": 10,
            "registeredgirls": 12,
            "status": True
        }
        resp = self.client.post(f"{BASE_URL}timetables/", payload)
        assert resp.status_code == 201
        tt_id = resp.json()["id"]

        resp2 = self.client.get(f"{BASE_URL}timetables/{tt_id}/")
        assert resp2.status_code == 200

        resp3 = self.client.patch(f"{BASE_URL}timetables/{tt_id}/", {"registeredboys": 15})
        assert resp3.status_code == 200

        resp4 = self.client.delete(f"{BASE_URL}timetables/{tt_id}/")
        assert resp4.status_code == 204