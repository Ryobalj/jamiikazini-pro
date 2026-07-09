# logistics/tests/test_driver.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from kiini.models import Institution
from logistics.models import TransportProvider, Driver


@pytest.mark.django_db
class TestDriverAPI:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def institution(self):
        return Institution.objects.create(name="Sample Institution")

    @pytest.fixture
    def user(self, institution):
        return User.objects.create_user(
            email="provider@example.com",
            password="pass1234",
            role="TRANSPORTER",
            full_name="Provider User",
            institution=institution
        )

    @pytest.fixture
    def provider(self, user, institution):
        return TransportProvider.objects.create(user=user, institution=institution)

    @pytest.fixture
    def auth_client(self, client, user, provider):
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def driver(self, provider):
        return Driver.objects.create(
            transport_provider=provider,
            full_name="John Driver",
            license_number="LIC12345",
            phone_number="0755555555"
        )

    def test_create_driver_success(self, auth_client):
        url = reverse('logistics:driver-list')
        data = {
            "full_name": "Driver One",
            "license_number": "DL10001",
            "phone_number": "0712345678"
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['full_name'] == "Driver One"

    def test_list_drivers(self, auth_client, driver):
        url = reverse('logistics:driver-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_update_driver(self, auth_client, driver):
        url = reverse('logistics:driver-detail', args=[driver.id])
        payload = {
            "phone_number": "0788888888"
        }
        response = auth_client.patch(url, payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['phone_number'] == "0788888888"

    def test_delete_driver(self, auth_client, driver):
        url = reverse('logistics:driver-detail', args=[driver.id])
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Driver.objects.count() == 0

    def test_license_number_must_be_unique(self, auth_client, provider):
        # Create first driver
        Driver.objects.create(
            transport_provider=provider,
            full_name="Driver A",
            license_number="DLX001"
        )

        # Attempt to create another with same license
        url = reverse('logistics:driver-list')
        data = {
            "full_name": "Driver B",
            "license_number": "DLX001",
            "phone_number": "0700000000"
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'license_number' in response.data

    def test_unauthorized_user_cannot_access(self, client, driver):
        url = reverse('logistics:driver-detail', args=[driver.id])
        response = client.get(url)
        assert response.status_code in [401, 403]