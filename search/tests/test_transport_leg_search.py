# search/tests/test_transport_leg_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)

from django.urls import reverse
from rest_framework.test import APITestCase
from logistics.models.transport_leg import TransportLeg
from logistics.models.shipment import Shipment
from logistics.models.transport_provider import TransportProvider
from accounts.models import User


class TransportLegSearchTest(APITestCase):

    def setUp(self):
        user = User.objects.create_user(username="leguser", password="test123")
        provider = TransportProvider.objects.create(user=user, provider_type="car", is_approved=True, location={"lat": -6.8, "lon": 39.2})
        shipment = Shipment.objects.create(status="in_transit", total_cost=50000)

        TransportLeg.objects.create(
            shipment=shipment,
            provider=provider,
            sequence_number=1,
            origin_name="Dar",
            destination_name="Dodoma",
            origin_coords={"lat": -6.8, "lon": 39.2},
            destination_coords={"lat": -6.2, "lon": 35.7},
            current_location={"lat": -6.6, "lon": 38.9},
            mode="truck",
            status="in_progress",
            base_fare=10000,
            distance_fee=5000,
            tax=1800,
            jamiikazini_commission=1200,
            total_cost=18000
        )

    def test_leg_search_by_name(self):
        url = reverse('transport-leg-search')
        response = self.client.get(url, {'q': 'Dodoma'})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['total'], 1)