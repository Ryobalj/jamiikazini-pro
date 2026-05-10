import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from kiini.models.institution import Institution
from security.permissions.require_2fa import Require2FA


# Dummy view for testing permission
class DummySecureView(APIView):
    permission_classes = [IsAuthenticated, Require2FA]

    def get(self, request):
        return Response({"detail": "Success"})


@pytest.mark.django_db
class TestRequire2FAPermission:

    def setup_method(self):
        self.factory = APIRequestFactory()
        self.institution = Institution.objects.create(name="Test Org", domain="testorg")

    def get_response(self, user):
        request = self.factory.get("/secure/")
        force_authenticate(request, user=user)
        view = DummySecureView.as_view()
        response = view(request)
        return response

    def test_admin_without_2fa_is_denied(self):
        user = User.objects.create_user(
            email="admin@test.com",
            password="password123",
            full_name="Admin No2FA",
            role="ADMIN",
            institution=self.institution,
            is_2fa_enabled=False,
        )
        response = self.get_response(user)
        assert response.status_code == 403

    def test_institution_admin_without_2fa_is_denied(self):
        user = User.objects.create_user(
            email="instadmin@test.com",
            password="password123",
            full_name="InstAdmin No2FA",
            role="INSTITUTION_ADMIN",
            institution=self.institution,
            is_2fa_enabled=False,
        )
        response = self.get_response(user)
        assert response.status_code == 403

    def test_client_without_2fa_is_denied(self):
        user = User.objects.create_user(
            email="client@test.com",
            password="password123",
            full_name="Client No2FA",
            role="CLIENT",
            institution=self.institution,
            is_2fa_enabled=False,
        )
        response = self.get_response(user)
        assert response.status_code == 403

    def test_client_with_2fa_is_allowed(self):
        user = User.objects.create_user(
            email="client2@test.com",
            password="password123",
            full_name="Client With2FA",
            role="CLIENT",
            institution=self.institution,
            is_2fa_enabled=True,
        )
        response = self.get_response(user)
        assert response.status_code == 200

    def test_provider_with_2fa_is_allowed(self):
        user = User.objects.create_user(
            email="provider@test.com",
            password="password123",
            full_name="Provider User",
            role="PROVIDER",
            institution=self.institution,
            is_2fa_enabled=True,
        )
        response = self.get_response(user)
        assert response.status_code == 200

    def test_transporter_without_2fa_is_denied(self):
        user = User.objects.create_user(
            email="transporter@test.com",
            password="password123",
            full_name="Transporter User",
            role="TRANSPORTER",
            institution=self.institution,
            is_2fa_enabled=False,
        )
        response = self.get_response(user)
        assert response.status_code == 403