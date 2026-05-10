# logistics/tests/test_transport_leg.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.gis.geos import Point
from logistics.models import TransportLeg, LegStatusLog, TransportProvider, Shipment
from accounts.models import User
from businesses.models.product import Product


User = get_user_model()

class TransportLegTrackURLTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='client@example.com', password='pass1234')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.provider = TransportProvider.objects.create(
            user=self.user,
            name='JamiiTransport',
            slug='jamii',
            contact_info='078999888'
        )

        self.product = Product.objects.create(name='Test Product', price=1000)

        self.receiver = User.objects.create_user(email='receiver@example.com', password='pass1234')
        self.shipment = Shipment.objects.create(
            sender=self.user,
            receiver=self.receiver,
            product=self.product,
            preferred_transport_modes=["ROAD"],
            route_details="From A to B",
            transport_fee=2000,
            jamiikazini_commission=500,
        )

        self.leg = TransportLeg.objects.create(
            shipment=self.shipment,
            provider=self.provider,
            sequence_number=1,
            origin_name="Dar",
            destination_name="Arusha",
            mode="ROAD",
            status="PENDING"
        )

    def test_transport_leg_track_url_returns_correct_url(self):
        url = reverse('transportleg-track-url', kwargs={'pk': self.leg.pk})
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
    def provider(self):
        return TransportProvider.objects.create(name="Provider A")

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
        return Product.objects.create(
            name="Test Product",
            description="Test",
            price=100
        )

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
        url = reverse("transport-legs-list")
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
        url = reverse("transport-legs-update-status", args=[leg.id])
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
        url = reverse("leg-status-logs-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(str(log.status) in str(entry["status"]) for entry in response.data)