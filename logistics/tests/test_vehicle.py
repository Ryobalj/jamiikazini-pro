# logistics/tests/test_vehicle.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.exceptions import ValidationError

from accounts.models import User
from logistics.models import Vehicle, TransportProvider, Driver


@pytest.mark.django_db
class TestVehicleAPI:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def provider_user(self):
        return User.objects.create_user(
            email="provider@example.com",
            password="strongpass123",
            full_name="Provider User",
            role="TRANSPORTER"
        )

    @pytest.fixture
    def provider(self, provider_user):
        return TransportProvider.objects.create(user=provider_user)

    @pytest.fixture
    def auth_client(self, client, provider_user):
        client.force_authenticate(user=provider_user)
        return client

    @pytest.fixture
    def vehicle(self, provider):
        return Vehicle.objects.create(
            provider=provider,
            vehicle_type="canter",
            registration_number="T123ABC"
        )

    def test_create_vehicle(self, auth_client, provider):
        url = reverse('logistics:vehicle-list')
        payload = {
            "provider": str(provider.id),
            "vehicle_type": "canter",
            "registration_number": "T567DEF"
        }
        response = auth_client.post(url, payload, format='json')
        assert response.status_code == 201
        assert response.data['registration_number'] == "T567DEF"

    def test_list_vehicles(self, auth_client, vehicle):
        url = reverse('logistics:vehicle-list')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_update_vehicle(self, auth_client, vehicle):
        url = reverse('logistics:vehicle-detail', args=[vehicle.id])
        payload = {"model_name": "Isuzu"}
        response = auth_client.patch(url, payload, format='json')
        assert response.status_code == 200
        assert response.data['model_name'] == "Isuzu"

    def test_delete_vehicle(self, auth_client, vehicle):
        url = reverse('logistics:vehicle-detail', args=[vehicle.id])
        response = auth_client.delete(url)
        assert response.status_code == 204

    def test_unauthorized_user_cannot_modify(self, client, vehicle):
        url = reverse('logistics:vehicle-detail', args=[vehicle.id])
        response = client.patch(url, {"model_name": "Unauthorized"}, format='json')
        assert response.status_code in [401, 403]

    def test_cannot_assign_more_than_two_drivers(self, vehicle, provider):
        # Tengeneza madereva 3
        driver1 = Driver.objects.create(full_name="Driver One", transport_provider=provider, license_number="VDL001")
        driver2 = Driver.objects.create(full_name="Driver Two", transport_provider=provider, license_number="VDL002")
        driver3 = Driver.objects.create(full_name="Driver Three", transport_provider=provider, license_number="VDL003")

        # Ongeza wawili wa mwanzo
        vehicle.drivers.add(driver1, driver2)

        # Jaribu kuongeza wa tatu
        vehicle.drivers.add(driver3)

        with pytest.raises(ValidationError) as excinfo:
            vehicle.full_clean()

        assert "maximum of 2 drivers" in str(excinfo.value).lower()