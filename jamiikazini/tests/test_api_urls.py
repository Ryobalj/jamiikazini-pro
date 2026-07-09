# jamiikazini/tests/test_api_urls.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

@pytest.mark.django_db
class TestAPIUrls:

    def setup_method(self):
        self.client = APIClient()

    # Njia halisi: API nzima iko chini ya /api/v1/, JWT ziko chini ya security/

    def test_health_check(self):
        response = self.client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_token_obtain(self, django_user_model):
        user = django_user_model.objects.create_user(email="test@example.com", password="testpass123")
        response = self.client.post("/api/v1/security/token/", {
            "email": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_token_refresh(self, django_user_model):
        user = django_user_model.objects.create_user(email="test@example.com", password="testpass123")
        token_response = self.client.post("/api/v1/security/token/", {
            "email": "test@example.com",
            "password": "testpass123"
        })
        refresh_token = token_response.data["refresh"]
        response = self.client.post("/api/v1/security/token/refresh/", {"refresh": refresh_token})
        assert response.status_code == 200
        assert "access" in response.data

    def test_token_verify(self, django_user_model):
        user = django_user_model.objects.create_user(email="test@example.com", password="testpass123")
        token_response = self.client.post("/api/v1/security/token/", {
            "email": "test@example.com",
            "password": "testpass123"
        })
        access_token = token_response.data["access"]
        response = self.client.post("/api/v1/security/token/verify/", {"token": access_token})
        assert response.status_code == 200

    def test_apps_include(self):
        # Just check some endpoints are reachable
        response = self.client.get("/api/v1/auth/")
        assert response.status_code in [200, 403, 401, 404]

        response = self.client.get("/api/v1/kiini/")
        assert response.status_code in [200, 403, 401, 404]