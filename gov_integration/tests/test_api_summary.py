# gov_integration/tests/test_api_summary.py

import pytest
from rest_framework.test import APIClient
from kiini.models import Institution
from django.contrib.auth import get_user_model
from gov_integration.models import VerificationRequest, CountryConfig, ServiceType

User = get_user_model()

@pytest.mark.django_db
def test_summary_counts():
    # Create necessary objects
    inst = Institution.objects.create(name="Test Inst", domain="test")
    country = CountryConfig.objects.create(code='TZ', name='Tanzania', currency='TZS')
    service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)

    user = User.objects.create_user(
        email='dash@example.com', 
        password='test', 
        role='CLIENT', 
        full_name='Dash'
    )
    user.institution = inst
    user.save()

    admin = User.objects.create_user(
        email='admin@example.com',
        password='adminpass',
        role='INSTITUTION_ADMIN',
        full_name='Admin User'
    )
    admin.institution = inst
    admin.save()

    client = APIClient()
    client.force_authenticate(user=admin)
    client.defaults['HTTP_HOST'] = 'test.localhost'

    VerificationRequest.objects.create(user=user, institution=inst, country='TZ', service=service, status='PENDING', payload={})
    VerificationRequest.objects.create(user=user, institution=inst, country='TZ', service=service, status='VERIFIED', payload={})
    VerificationRequest.objects.create(user=user, institution=inst, country='TZ', service=service, status='FAILED', payload={})

    response = client.get('/api/verify/summary/')
    data = response.json()

    assert response.status_code == 200
    assert data['pending'] == 1
    assert data['verified'] == 1
    assert data['failed'] == 1