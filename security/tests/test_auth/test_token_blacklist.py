import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from kiini.models.institution import Institution


@pytest.mark.django_db
class TestTokenBlacklist:

    @pytest.fixture
    def create_user(self):
        def _create_user(**kwargs):
            institution = Institution.objects.create(name="Test Institution")
            return User.objects.create_user(
                email=kwargs.get("email", "logoutuser@example.com"),
                password=kwargs.get("password", "logoutpass123"),
                full_name=kwargs.get("full_name", "Logout User"),
                role=kwargs.get("role", "CLIENT"),
                institution=institution
            )
        return _create_user

    def test_token_blacklist_success(self, create_user):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
    
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        url = reverse("security_jwt:token_blacklist")
        response = client.post(url, {"refresh": refresh_token})

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_205_RESET_CONTENT]
        # Optional check if detail exists
        if response.data:
            assert "detail" in response.data

    def test_token_blacklist_invalid_token(self, create_user):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
    
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        url = reverse("security_jwt:token_blacklist")
        response = client.post(url, {"refresh": "invalidtoken"})
    
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data

    def test_blacklisted_refresh_token_reuse_fails(self, create_user):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        refresh_token_str = str(refresh)
    
        # Blacklist the refresh token
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        url = reverse("security_jwt:token_blacklist")
        client.post(url, {"refresh": refresh_token_str})
    
        # Try using the blacklisted refresh token again
        refresh_url = reverse("security_jwt:token_refresh")
        response = client.post(refresh_url, {"refresh": refresh_token_str})
    
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        assert "blacklisted" in response.data["detail"].lower()
