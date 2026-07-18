# security/tests/test_phone_verification.py

import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status

pytestmark = pytest.mark.django_db

REQUEST_URL = "/api/v1/security/phone/request/"
VERIFY_URL = "/api/v1/security/phone/verify/"


@pytest.fixture
def api():
    return APIClient()


def test_request_requires_authentication(api):
    response = api.post(REQUEST_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_request_fails_without_phone_number(api, user_factory):
    user = user_factory()
    api.force_authenticate(user=user)
    response = api.post(REQUEST_URL)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("jamiitasks.tasks.notifications.send_sms_task.delay")
def test_request_sends_sms_regardless_of_preferred_method(mock_send_sms, api, user_factory):
    user = user_factory(preferred_otp_method="EMAIL")
    user.phone_number = "+255700000000"
    user.save()
    api.force_authenticate(user=user)

    response = api.post(REQUEST_URL)

    assert response.status_code == status.HTTP_200_OK
    mock_send_sms.assert_called_once()
    user.refresh_from_db()
    assert user._otp_code  # generated even though preferred method is EMAIL


@patch("jamiitasks.tasks.notifications.send_sms_task.delay")
def test_request_fails_if_already_verified(mock_send_sms, api, user_factory):
    user = user_factory()
    user.phone_number = "+255700000000"
    user.is_phone_verified = True
    user.save()
    api.force_authenticate(user=user)

    response = api.post(REQUEST_URL)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_verify_sets_is_phone_verified_on_correct_code(api, user_factory):
    user = user_factory()
    user.phone_number = "+255700000000"
    user.save()
    code = user.generate_otp(method="SMS")
    api.force_authenticate(user=user)

    response = api.post(VERIFY_URL, {"code": code}, format="json")

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.is_phone_verified is True


def test_verify_rejects_wrong_code(api, user_factory):
    user = user_factory()
    user.phone_number = "+255700000000"
    user.save()
    user.generate_otp(method="SMS")
    api.force_authenticate(user=user)

    response = api.post(VERIFY_URL, {"code": "000000"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    user.refresh_from_db()
    assert user.is_phone_verified is False


def test_verify_requires_code_field(api, user_factory):
    user = user_factory()
    api.force_authenticate(user=user)
    response = api.post(VERIFY_URL, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
