# logistics/tests/test_transport_leg_edge.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.gis.geos import Point
from logistics.models import TransportLeg, LegStatusLog, Shipment, TransportProvider
from accounts.models import User
from businesses.models.product import Product


@pytest.mark.django_db
class TestTransportLegEdgeCases:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email="client@example.com", password="pass123",
            full_name="Client User", role="CLIENT"
        )

    @pytest.fixture
    def another_user(self):
        return User.objects.create_user(
            email="other@example.com", password="pass123",
            full_name="Other User", role="CLIENT"
        )

    @pytest.fixture
    def provider(self):
        return TransportProvider.objects.create(name="Edge Provider")

    @pytest.fixture
    def shipment(self, user, product):
        return Shipment.objects.create(
            product=product,
            sender=user,
            receiver=user,
            total_cost=2000
        )

    @pytest.fixture
    def product(self):
        return Product.objects.create(name="Edge Product", description="Test", price=100)

    @pytest.fixture
    def leg(self, shipment, provider):
        return TransportLeg.objects.create(
            shipment=shipment,
            provider=provider,
            sequence_number=1,
            origin_name="Start",
            origin_coords=Point(39.2, -6.8),
            destination_name="End",
            destination_coords=Point(39.3, -6.7),
            mode="TRUCK",
            total_cost=1500
        )

    def test_unauthorized_status_update(self, client, leg):
        url = reverse("transport-legs-update-status", args=[leg.id])
        response = client.post(url, {"status": "IN_TRANSIT"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_status_value(self, client, user, leg):
        client.force_authenticate(user=user)
        url = reverse("transport-legs-update-status", args=[leg.id])
        response = client.post(url, {"status": "INVALID_STATUS"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthorized_user_cannot_update_leg(self, client, another_user, leg):
        client.force_authenticate(user=another_user)
        url = reverse("transport-legs-update-status", args=[leg.id])
        response = client.post(url, {"status": "IN_TRANSIT"}, format="json")
        # Depending on your access control, either 403 Forbidden or 404 Not Found
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_duplicate_status_logs(self, client, user, leg):
        client.force_authenticate(user=user)
        url = reverse("transport-legs-update-status", args=[leg.id])
        client.post(url, {"status": "IN_TRANSIT"}, format="json")
        client.post(url, {"status": "IN_TRANSIT"}, format="json")

        logs = LegStatusLog.objects.filter(leg=leg, status="IN_TRANSIT")
        assert logs.count() == 2  # If duplicates allowed; else should test uniqueness