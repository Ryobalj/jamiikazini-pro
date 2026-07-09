# logistics/tests/test_transport_leg.py

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.gis.geos import Point
from logistics.models import TransportLeg, LegStatusLog, TransportProvider, Shipment
from businesses.models.product import Product


User = get_user_model()

class TransportLegTrackURLTests(APITestCase):
    def setUp(self):
        from kiini.models import Institution
        inst = Institution.objects.create(name="Jamii", domain="jamii.jamiikazini.com")
        self.user = User.objects.create_user(email='client@example.com', password='pass1234', institution=inst)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.provider = TransportProvider.objects.create(user=self.user)

        from logistics.factories import BusinessFactory
        self.product = Product.objects.create(
            name='Test Product', slug='test-product-leg', price=1000,
            business=BusinessFactory(),
        )

        self.receiver = User.objects.create_user(email='receiver@example.com', password='pass1234')
        self.shipment = Shipment.objects.create(
            sender=self.user,
            receiver=self.receiver,
            product=self.product,
            route_details={"start": [39.2, -6.8], "end": [39.3, -6.9]},
            transport_fee=2000,
            jamiikazini_commission=500,
            total_cost=2500,
        )

        self.leg = TransportLeg.objects.create(
            shipment=self.shipment,
            provider=self.provider,
            sequence_number=1,
            origin_name="Dar",
            origin_coords=Point(39.2, -6.8),
            destination_name="Arusha",
            destination_coords=Point(36.7, -3.4),
            mode="ROAD",
            status="PENDING",
            total_cost=1000,
        )

    def test_transport_leg_track_url_returns_correct_url(self):
        url = reverse('logistics:transport-legs-track-url', kwargs={'pk': self.leg.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('track_url', response.data)
        self.assertTrue(response.data['track_url'].startswith('https://jamii.'))


@pytest.mark.django_db
class TestTransportLegAPI:

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
    def provider(self, user):
        return TransportProvider.objects.create(user=user)

    @pytest.fixture
    def shipment(self, user, product):
        return Shipment.objects.create(
            product=product,
            sender=user,
            receiver=user,
            total_cost=10000
        )

    @pytest.fixture
    def product(self):
        from logistics.factories import ProductFactory
        return ProductFactory(name="Test Product", description="Test", price=100)

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
            total_cost=1000
        )

    def test_create_leg(self, client, user, shipment, provider):
        client.force_authenticate(user=user)
        url = reverse("logistics:transport-legs-list")
        data = {
            "shipment": shipment.id,
            "provider": provider.id,
            "sequence_number": 1,
            "origin_name": "Dar",
            "origin_coords": {"type": "Point", "coordinates": [39.2, -6.8]},
            "destination_name": "Morogoro",
            "destination_coords": {"type": "Point", "coordinates": [37.7, -6.8]},
            "mode": "TRUCK",
            "total_cost": "2500.00"
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_leg_status(self, client, user, leg):
        client.force_authenticate(user=user)
        url = reverse("logistics:transport-legs-update-status", args=[leg.id])
        data = {
            "status": "DISPATCHED",
            "remarks": "Left warehouse"
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        leg.refresh_from_db()
        assert leg.status == "DISPATCHED"
        assert LegStatusLog.objects.filter(leg=leg, status="DISPATCHED").exists()

    def test_list_leg_status_logs(self, client, user, leg):
        log = LegStatusLog.objects.create(leg=leg, status="SCHEDULED", updated_by=user)
        client.force_authenticate(user=user)
        url = reverse("logistics:leg-status-logs-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(str(log.status) in str(entry["status"]) for entry in response.data)