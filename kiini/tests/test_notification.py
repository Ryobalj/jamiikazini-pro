# kiini/tests/test_notification.py

import pytest
from rest_framework.test import APIClient
from rest_framework import status

from kiini.models.notification import Notification, NotificationType
from kiini.helpers.notification_helper import notify_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def test_notify_user_creates_notification_with_defaults(user_factory):
    user = user_factory()
    notify_user(user, "Habari fulani.")

    notification = Notification.objects.get(user=user)
    assert notification.notification_type == NotificationType.SYSTEM
    assert notification.link is None
    assert notification.is_read is False


def test_notify_user_with_explicit_type_and_link(user_factory):
    user = user_factory()
    notify_user(user, "Oda mpya.", notification_type=NotificationType.ORDER, link="/orders/123")

    notification = Notification.objects.get(user=user)
    assert notification.notification_type == NotificationType.ORDER
    assert notification.link == "/orders/123"


def test_list_notifications_scoped_to_requesting_user(api, user_factory):
    me = user_factory()
    other = user_factory()
    notify_user(me, "Yangu")
    notify_user(other, "Ya mwingine")

    api.force_authenticate(user=me)
    response = api.get("/api/v1/kiini/notifications/")

    assert response.status_code == status.HTTP_200_OK
    messages = [row["message"] for row in response.data]
    assert messages == ["Yangu"]


def test_mark_read_flips_flag(api, user_factory):
    user = user_factory()
    notify_user(user, "Bado haijasomwa")
    notification = Notification.objects.get(user=user)

    api.force_authenticate(user=user)
    response = api.post(f"/api/v1/kiini/notifications/{notification.id}/mark-read/")

    assert response.status_code == status.HTTP_200_OK
    notification.refresh_from_db()
    assert notification.is_read is True


def test_mark_read_rejects_another_users_notification(api, user_factory):
    owner = user_factory()
    intruder = user_factory()
    notify_user(owner, "Siri")
    notification = Notification.objects.get(user=owner)

    api.force_authenticate(user=intruder)
    response = api.post(f"/api/v1/kiini/notifications/{notification.id}/mark-read/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    notification.refresh_from_db()
    assert notification.is_read is False


def test_mark_all_read(api, user_factory):
    user = user_factory()
    notify_user(user, "Moja")
    notify_user(user, "Mbili")

    api.force_authenticate(user=user)
    response = api.post("/api/v1/kiini/notifications/mark-all-read/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["updated"] == 2
    assert Notification.objects.filter(user=user, is_read=False).count() == 0
