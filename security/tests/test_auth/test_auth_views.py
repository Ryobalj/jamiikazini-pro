import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from kiini.models.institution import Institution
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestAuthViews:

    @pytest.fixture
    def create_user(self):
        def _create_user(**kwargs):
            institution = Institution.objects.create(name="Test Institution")
            return User.objects.create_user(
                email=kwargs.get("email", "test@example.com"),
                password=kwargs.get("password", "strongpassword123"),
                full_name=kwargs.get("full_name", "Test User"),
                role=kwargs.get("role", "CLIENT"),
                institution=institution,
                is_2fa_enabled=kwargs.get("is_2fa_enabled", False),
                _2fa_secret=kwargs.get("_2fa_secret", None)
            )
        return _create_user

    # ✅ Helper to simulate valid ReCAPTCHA
    def recaptcha_data(self):
        return {"recaptcha_token": "PASSED"}  # simulate always-passing in tests

    def test_unified_login_success_without_2fa(self, create_user):
        user = create_user()
        client = APIClient()

        url = reverse("jamii_auth:unified_login")
        response = client.post(url, {
            "email": user.email,
            "password": "strongpassword123",
            **self.recaptcha_data()
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["detail"] == "Login successful."

    def test_unified_login_requires_2fa(self, create_user):
        user = create_user(
            is_2fa_enabled=True,
            _2fa_secret="JBSWY3DPEHPK3PXP"
        )
        client = APIClient()
        url = reverse("jamii_auth:unified_login")
        response = client.post(url, {
            "email": user.email,
            "password": "strongpassword123",
            **self.recaptcha_data()
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "2FA required."
        assert response.data["2fa_required"] is True

    def test_unified_login_failure_invalid_credentials(self):
        client = APIClient()
        url = reverse("jamii_auth:unified_login")
        response = client.post(url, {
            "email": "nonexistent@example.com",
            "password": "wrongpass",
            **self.recaptcha_data()
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in str(response.data["detail"])

    def test_login_sets_cookies_without_2fa(self, create_user):
        user = create_user()
        client = APIClient()
        url = reverse("jamii_auth:unified_login") + "?use_cookies=true"

        response = client.post(url, {
            "email": user.email,
            "password": "strongpassword123",
            **self.recaptcha_data()
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.cookies
        assert "refresh" in response.cookies

    def test_login_cookies_not_set_if_2fa_required(self, create_user):
        user = create_user(
            is_2fa_enabled=True,
            _2fa_secret="JBSWY3DPEHPK3PXP"
        )
        client = APIClient()
        url = reverse("jamii_auth:unified_login") + "?use_cookies=true"

        response = client.post(url, {
            "email": user.email,
            "password": "strongpassword123",
            **self.recaptcha_data()
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "access" not in response.cookies
        assert "refresh" not in response.cookies

    def test_logout_success(self, create_user):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("jamii_auth:logout")
        response = client.post(url, {"refresh": refresh_token})

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["detail"] == "Logout successful."

    def test_logout_invalid_token(self, create_user):
        user = create_user()

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("jamii_auth:logout")
        response = client.post(url, {"refresh": "invalidtoken"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data