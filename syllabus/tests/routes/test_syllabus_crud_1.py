# syllabus/tests/test_syllabus_crud_1.py

import pytest
import uuid
from accounts.models import User
from syllabus.models.annual_calendar import AnnualCalendar
from syllabus.models.class_level import ClassLevel
from syllabus.models.lesson_sentence import LessonSentence
from django.db.models import signals
from jamiiwallet.models.wallet import Wallet

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
class TestSyllabusAdminOnlyCRUD:

    @pytest.fixture(autouse=True)
    def setup(self, user_factory, api_client):
        self.admin = user_factory(role="ADMIN")
        self.client = api_client
        self.client.force_authenticate(self.admin)

    # -------------------------
    # AnnualCalendar CRUD
    # -------------------------
    def test_annual_calendar_crud(self):
        payload = {
            "year": 2025,
            "institute": f"Test Institute {uuid.uuid4().hex[:6]}",
            "total_learning_days": 194
        }
        # Create
        resp = self.client.post(f"{BASE_URL}annual-calendars/", payload)
        assert resp.status_code == 201, resp.json()
        ac_id = resp.json()["id"]

        # Read
        resp2 = self.client.get(f"{BASE_URL}annual-calendars/{ac_id}/")
        assert resp2.status_code == 200

        # Update
        resp3 = self.client.patch(f"{BASE_URL}annual-calendars/{ac_id}/", {"total_learning_days": 200})
        assert resp3.status_code == 200

        # Delete
        resp4 = self.client.delete(f"{BASE_URL}annual-calendars/{ac_id}/")
        assert resp4.status_code == 204

    # -------------------------
    # ClassLevel CRUD
    # -------------------------
    def test_class_level_crud(self):
        name = f"Grade 2 {uuid.uuid4().hex[:6]}"
        payload = {"name": name, "order": 2}

        # Create
        resp = self.client.post(f"{BASE_URL}class-levels/", payload)
        assert resp.status_code == 201
        cl_id = resp.json()["id"]

        # Read
        resp2 = self.client.get(f"{BASE_URL}class-levels/{cl_id}/")
        assert resp2.status_code == 200

        # Update
        resp3 = self.client.patch(f"{BASE_URL}class-levels/{cl_id}/", {"order": 3})
        assert resp3.status_code == 200

        # Delete
        resp4 = self.client.delete(f"{BASE_URL}class-levels/{cl_id}/")
        assert resp4.status_code == 204

    # -------------------------
    # LessonSentence CRUD
    # -------------------------
    def test_lesson_sentence_crud(self):
        text = f"Fundisha kwa vitendo {uuid.uuid4().hex[:6]}"
        payload = {"teaching_sw": text, "teaching_en": "Teach practically"}

        # Create
        resp = self.client.post(f"{BASE_URL}lesson-sentences/", payload)
        assert resp.status_code == 201
        ls_id = resp.json()["id"]

        # Read
        resp2 = self.client.get(f"{BASE_URL}lesson-sentences/{ls_id}/")
        assert resp2.status_code == 200

        # Update
        resp3 = self.client.patch(f"{BASE_URL}lesson-sentences/{ls_id}/", {"teaching_sw": "Sentensi iliyosasishwa."})
        assert resp3.status_code == 200

        # Delete
        resp4 = self.client.delete(f"{BASE_URL}lesson-sentences/{ls_id}/")
        assert resp4.status_code == 204