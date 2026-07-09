# search/tests/test_transport_provider_verification_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)
from django.urls import reverse
from rest_framework.test import APIClient
from logistics.models.transport_provider_verification import TransportProviderVerification
from accounts.models import User
from kiini.models.institution import Institution
from gov_integration.models.verification_request import VerificationRequest
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections
from search.documents.transport_provider_verification_document import TransportProviderVerificationDocument

pytestmark = pytest.mark.django_db

@pytest.fixture
def setup_verification_data():
    institution = Institution.objects.create(name="Institution One")
    user = User.objects.create_user(username="driver1", email="driver1@example.com", password="testpass")
    vr = VerificationRequest.objects.create()

    tpv = TransportProviderVerification.objects.create(
        user=user,
        institution=institution,
        overall_status="verified",
        notes="All documents verified",
        nida_verification=vr,
        driving_license_verification=vr,
        vehicle_license_verification=vr,
        latra_permit_verification=vr
    )

    # Index to Elasticsearch
    doc = TransportProviderVerificationDocument()
    doc.update(tpv)

    return tpv

def refresh_index():
    connections.get_connection().indices.refresh(index='transport_provider_verifications')

def test_search_transport_provider_verification(setup_verification_data):
    refresh_index()
    client = APIClient()
    url = reverse('search-transport-verifications')
    response = client.get(url, {'q': 'verified'})

    assert response.status_code == 200
    assert 'results' in response.data
    assert any('verified' in r['overall_status'] for r in response.data['results'])