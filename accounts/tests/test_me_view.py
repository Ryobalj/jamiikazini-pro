# accounts/tests/test_me_view.py

import pytest
from rest_framework.test import APIClient
from rest_framework import status

pytestmark = pytest.mark.django_db

ME_URL = "/api/v1/auth/me/"


def test_patch_updates_whitelisted_field(user_factory):
    user = user_factory(preferred_otp_method="SMS")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.patch(ME_URL, {"preferred_otp_method": "EMAIL"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["preferred_otp_method"] == "EMAIL"
    user.refresh_from_db()
    assert user.preferred_otp_method == "EMAIL"


def test_patch_rejects_invalid_otp_method(user_factory):
    user = user_factory(preferred_otp_method="SMS")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.patch(ME_URL, {"preferred_otp_method": "CARRIER_PIGEON"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert user.preferred_otp_method == "SMS"


def test_patch_ignores_non_whitelisted_fields(user_factory):
    user = user_factory(role="CLIENT")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.patch(ME_URL, {"role": "ADMIN", "is_identity_verified": True}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert user.role == "CLIENT"
    assert user.is_identity_verified is False


def test_patch_full_name(user_factory):
    user = user_factory(full_name="Old Name")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.patch(ME_URL, {"full_name": "New Name"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.full_name == "New Name"


def test_patch_requires_authentication():
    api = APIClient()
    response = api.patch(ME_URL, {"preferred_otp_method": "EMAIL"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
