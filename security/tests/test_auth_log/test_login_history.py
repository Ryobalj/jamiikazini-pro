# security/tests/test_security_log/test_login_history.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, LoginHistory
from kiini.models.institution import Institution
from datetime import datetime, timedelta

@pytest.mark.django_db
class TestLoginHistoryView:

    @pytest.fixture
    def institution(self):
        return Institution.objects.create(name="Test Institution")

    @pytest.fixture
    def create_user(self, institution):
        def _create_user(**kwargs):
            return User.objects.create_user(
                email=kwargs.get("email", "user@example.com"),
                password=kwargs.get("password", "password123"),
                full_name=kwargs.get("full_name", "Test User"),
                role=kwargs.get("role", "CLIENT"),
                institution=institution
            )
        return _create_user

    @pytest.fixture
    def create_login_history(self, create_user):
        def _create_login_history(user, was_successful=True, days_ago=0, ip_address="127.0.0.1", user_agent="TestAgent"):
            login_time = datetime.now() - timedelta(days=days_ago)
            return LoginHistory.objects.create(
                user=user,
                was_successful=was_successful,
                login_time=login_time,
                ip_address=ip_address,
                user_agent=user_agent
            )
        return _create_login_history

    def test_user_can_view_their_own_login_history(self, create_user, create_login_history):
        user = create_user()
        create_login_history(user=user)
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("security_log:login_history")  # Adjust if your namespace/path differs
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['user'] == user.id

    def test_admin_can_view_another_user_login_history(self, create_user, create_login_history):
        admin = create_user(email="admin@example.com", role="ADMIN")
        normal_user = create_user(email="normal@example.com")
        create_login_history(user=normal_user)
        client = APIClient()
        client.force_authenticate(user=admin)

        url = reverse("security_log:login_history") + f"?user_id={normal_user.id}"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['user'] == normal_user.id

    def test_filter_login_history_by_date(self, create_user, create_login_history):
        user = create_user()
        create_login_history(user=user, days_ago=1)
        create_login_history(user=user, days_ago=0)
        client = APIClient()
        client.force_authenticate(user=user)

        target_date = (datetime.now() - timedelta(days=1)).date().isoformat()
        url = reverse("security_log:login_history") + f"?date={target_date}"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for entry in response.data['results']:
            assert entry['login_time'].startswith(target_date)

    def test_filter_by_successful_logins(self, create_user, create_login_history):
        user = create_user()
        create_login_history(user=user, was_successful=True)
        create_login_history(user=user, was_successful=False)
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("security_log:login_history") + "?was_successful=true"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert all(entry['was_successful'] is True for entry in response.data['results'])

    def test_unauthorized_user_cannot_delete_history(self, create_user):
        user = create_user(role="CLIENT")
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("security_log:login_history")
        response = client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_all_history_or_specific_user(self, create_user, create_login_history):
        admin = create_user(role="ADMIN")
        user1 = create_user(email="user1@example.com")
        user2 = create_user(email="user2@example.com")

        create_login_history(user=user1)
        create_login_history(user=user2)
        client = APIClient()
        client.force_authenticate(user=admin)

        # Delete specific user's login history
        url = reverse("security_log:login_history") + f"?user_id={user1.id}"
        response = client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert LoginHistory.objects.filter(user=user1).count() == 0
        assert LoginHistory.objects.filter(user=user2).count() > 0

        # Delete all login history
        url = reverse("security_log:login_history")
        response = client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert LoginHistory.objects.count() == 0