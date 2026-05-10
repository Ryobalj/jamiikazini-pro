import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from kiini.models.institution import Institution


@pytest.mark.django_db
class TestTokenVerify:

    @pytest.fixture
    def create_user(self):
        def _create_user(**kwargs):
            institution = Institution.objects.create(name="Test Institution")
            return User.objects.create_user(
                email=kwargs.get("email", "verifyuser@example.com"),
                password=kwargs.get("password", "verifypass123"),
                full_name=kwargs.get("full_name", "Verify User"),
                role=kwargs.get("role", "CLIENT"),
                institution=institution
            )
        return _create_user

    def test_token_verify_success(self, create_user):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        url = reverse("security_jwt:token_verify")
        response = client.post(url, {"token": access_token})

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

    def test_token_verify_invalid(self):
        client = APIClient()
        url = reverse("security_jwt:token_verify")
        response = client.post(url, {"token": "invalidaccesstoken"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data