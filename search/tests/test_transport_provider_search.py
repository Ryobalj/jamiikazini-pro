# search/tests/test_transport_provider_search.py

from django.urls import reverse
from rest_framework.test import APITestCase
from accounts.models import User
from kiini.models.institution import Institution
from logistics.models.transport_provider import TransportProvider
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections
from search.documents.transport_provider_document import TransportProviderDocument


class TransportProviderSearchTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.institution = Institution.objects.create(name="Test Institution")
        cls.user1 = User.objects.create_user(username="john_doe", email="john@example.com", password="pass123")
        cls.user2 = User.objects.create_user(username="jane_doe", email="jane@example.com", password="pass456")

        cls.provider1 = TransportProvider.objects.create(
            user=cls.user1,
            institution=cls.institution,
            provider_type="bike",
            is_approved=True,
            location={"lat": -6.8, "lon": 39.2},
        )
        cls.provider2 = TransportProvider.objects.create(
            user=cls.user2,
            institution=cls.institution,
            provider_type="car",
            is_approved=True,
            location={"lat": -6.9, "lon": 39.3},
        )

        # Index transport providers into Elasticsearch
        cls.conn = connections.get_connection()
        TransportProviderDocument.init()
        bulk(cls.conn, (d.to_dict(True) | {"_id": d.meta.id} for d in TransportProviderDocument().update(TransportProvider.objects.all())))

    def test_basic_search(self):
        url = reverse('transport-provider-search')
        response = self.client.get(url, {'q': 'john'})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['total'], 1)

    def test_location_based_search(self):
        url = reverse('transport-provider-search')
        response = self.client.get(url, {'lat': -6.85, 'lon': 39.25, 'max_distance': 10})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['total'], 1)

    def test_pagination(self):
        url = reverse('transport-provider-search')
        response = self.client.get(url, {'page': 1, 'per_page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)