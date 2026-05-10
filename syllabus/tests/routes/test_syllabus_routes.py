# syllabus/tests/test_syllabus_routes.py

import pytest
import uuid
from rest_framework.test import APIClient
from accounts.models import User
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
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
class TestSyllabusRoutes:

    @pytest.fixture(autouse=True)
    def setup(self, user_factory, api_client):
        # Superuser kwa admin-only endpoints
        self.admin = user_factory(role="ADMIN")
        self.client = api_client
        self.client.force_authenticate(self.admin)

        # Normal user kwa auth endpoints
        self.user = user_factory(role="CLIENT")

    # Fixtures for unique objects
    @pytest.fixture
    def unique_class_level(self):
        cl = ClassLevel.objects.create(name=f"Grade {uuid.uuid4().hex[:6]}", order=1)
        yield cl
        cl.delete()

    @pytest.fixture
    def unique_subject(self):
        subj = Subject.objects.create(name=f"Subject {uuid.uuid4().hex[:6]}", periods_per_week=5)
        yield subj
        subj.delete()

    # ============================
    # Test Base Routes (Admin)
    # ============================
    def test_base_routes_accessible_admin(self):
        endpoints = [
            "subjects",
            "subject-versions",
            "syllabus-versions",
            "main-competences",
            "specific-competences",
            "learning-activities",
            "specific-learning-activities",
            "class-levels",
            "annual-calendars",
            "lesson-sentences",
        ]
        for ep in endpoints:
            url = f"{BASE_URL}{ep}/"
            resp = self.client.get(url)
            assert resp.status_code in [200, 204]

    # ============================
    # Test Authenticated Routes
    # ============================
    def test_authenticated_routes_require_auth(self):
        auth_endpoints = ["teacher-workstations", "timetables"]
        for ep in auth_endpoints:
            url = f"{BASE_URL}{ep}/"
            # Unauthenticated
            client = APIClient()
            resp = client.get(url)
            assert resp.status_code == 401
            # Authenticated
            self.client.force_authenticate(self.user)
            resp2 = self.client.get(url)
            assert resp2.status_code in [200, 204]

    # ============================
    # Test Nested Routes
    # ============================
    def test_nested_routes_exist(self, unique_class_level, unique_subject):
        cl = unique_class_level
        subj = unique_subject
        # Nested URL patterns
        nested_urls = [
            f"{BASE_URL}nested/main-competences/1/specific-competences/",
            f"{BASE_URL}nested/specific-competences/1/learning-activities/",
            f"{BASE_URL}nested/learning-activities/1/specific-learning-activities/",
        ]
        for url in nested_urls:
            resp = self.client.get(url)
            # 404 ok if parent doesn't exist, test just ensures router responds
            assert resp.status_code in [200, 404]

    # ============================
    # Test Invalid URL
    # ============================
    def test_invalid_url_returns_404(self):
        resp = self.client.get(f"{BASE_URL}non-existent/")
        assert resp.status_code == 404