# search/tests/test_shipment_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)
from django.urls import reverse
from rest_framework.test import APIClient
from model_bakery import baker
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections

from search.documents.shipment_document import ShipmentDocument
from logistics.models.shipment import Shipment  # REKebisho hapa
from accounts.models import User
from businesses.models.product import Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def es_client():
    return connections.get_connection()


@pytest.fixture
def setup_shipments(es_client):
    # Tengeneza users
    sender = baker.make(User, username='sender1', email='sender1@example.com')
    receiver = baker.make(User, username='receiver1', email='receiver1@example.com')

    # Tengeneza product
    product = baker.make(Product, name='Test Product', description='Test Desc')

    # Tengeneza shipment moja na route_details
    shipment = baker.make(
        Shipment,
        sender=sender,
        receiver=receiver,
        product=product,
        route_details={
            "origin": {"lat": -6.8, "lon": 39.28},
            "destination": {"lat": -6.9, "lon": 39.3}
        },
        status='in_transit',
        preferred_transport_modes=['truck'],
        _quantity=1
    )

    # Index kwenye Elasticsearch
    ShipmentDocument().update(shipment)
    es_client.indices.refresh(index='shipments')

    return shipment


def test_shipment_search_returns_results(setup_shipments):
    client = APIClient()
    url = reverse('search:shipment-search')

    response = client.get(url, {
        'origin_lat': -6.81,
        'origin_lon': 39.27,
        'distance': '10km'
    })

    assert response.status_code == 200
    data = response.json()
    assert data['count'] >= 1
    assert any(item['status'] == 'in_transit' for item in data['results'])


def test_shipment_search_filters_by_status(setup_shipments):
    client = APIClient()
    url = reverse('search:shipment-search')

    response = client.get(url, {
        'status': 'in_transit',
        'origin_lat': -6.81,
        'origin_lon': 39.27,
        'distance': '10km'
    })

    assert response.status_code == 200
    data = response.json()
    assert all(item['status'] == 'in_transit' for item in data['results'])
    
def test_shipment_search_filters_by_transport_mode(setup_shipments):
    client = APIClient()
    url = reverse('search:shipment-search')

    response = client.get(url, {
        'preferred_transport_modes': 'truck',
        'origin_lat': -6.81,
        'origin_lon': 39.27,
        'distance': '10km'
    })

    assert response.status_code == 200
    data = response.json()
    assert all('truck' in item['preferred_transport_modes'] for item in data['results'])


def test_shipment_search_filters_by_institution_id(setup_shipments):
    client = APIClient()
    shipment = setup_shipments
    shipment.institution_id = 99
    shipment.save()
    ShipmentDocument().update(shipment)

    url = reverse('search:shipment-search')
    client = APIClient()

    response = client.get(url, {
        'institution_id': 99,
        'origin_lat': -6.81,
        'origin_lon': 39.27,
        'distance': '10km'
    })

    assert response.status_code == 200
    data = response.json()
    assert all(item.get('institution_id') == 99 for item in data['results'])