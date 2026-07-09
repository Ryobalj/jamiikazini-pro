# search/tests/test_driver_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)

from django.urls import reverse
from rest_framework.test import APITestCase
from logistics.models.driver import Driver
from logistics.models.transport_provider import TransportProvider
from accounts.models import User


class DriverSearchTest(APITestCase):

    def setUp(self):
        user = User.objects.create_user(username="provuser", password="secret123")
        provider = TransportProvider.objects.create(
            user=user,
            name="Test Provider",
            license_number="TP-123",
            is_approved=True
        )
        Driver.objects.create(
            transport_provider=provider,
            full_name="Ali Ramadhani",
            license_number="D-456",
            phone_number="0712345678",
            is_verified=True,
            is_active=True
        )

    def test_search_driver_by_name(self):
        url = reverse("driver-search")
        response = self.client.get(url, {"q": "Ali"})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["total"], 1)