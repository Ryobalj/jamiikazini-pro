# security/tests/test_auth/test_token_refresh.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from kiini.models.institution import Institution


@pytest.mark.django_db
class TestTokenRefresh:

    @pytest.fixture
    def create_user(self):
        def _create_user(**kwargs):
            institution = Institution.objects.create(name="Test Institution")
            return User.objects.create_user(
                email=kwargs.get("email", "refreshuser@example.com"),
                password=kwargs.get("password", "refreshpass123"),
                full_name=kwargs.get("full_name", "Refresh User"),
                role=kwargs.get("role", "CLIENT"),
                institution=institution
            )
        return _create_user

    def test_token_refresh_success(self, create_user):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        client = APIClient()
        url = reverse("security_jwt:token_refresh")
        response = client.post(url, {"refresh": refresh_token})

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_token_refresh_failure_invalid_token(self):
        client = APIClient()
        url = reverse("security_jwt:token_refresh")
        response = client.post(url, {"refresh": "invalidtoken"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data