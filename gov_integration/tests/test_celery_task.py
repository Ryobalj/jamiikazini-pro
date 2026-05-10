import pytest
from unittest.mock import patch, Mock
from django.contrib.auth import get_user_model
from kiini.models import Institution
from gov_integration.models import VerificationRequest, ServiceType, CountryConfig, ServiceConfig, ApiEndpoint
from gov_integration.tasks import send_verification_request

User = get_user_model()

@pytest.mark.django_db
@patch("gov_integration.tasks.requests.post")
def test_send_verification_request_success(mock_post):
    inst = Institution.objects.create(name="Inst", domain="inst")
    country = CountryConfig.objects.create(code="TZ", name="Tanzania", currency="TZS")
    service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)

    user = User.objects.create_user(
        email="tester@example.com",
        password="123",
        role="CLIENT",
        full_name="Tester"
    )

    endpoint = ApiEndpoint.objects.create(name="NIDA API", country="TZ", base_url="https://nida.gov/api/")
    config = ServiceConfig.objects.create(endpoint=endpoint, access_token="testtoken", is_enabled=True)

    vreq = VerificationRequest.objects.create(
        user=user,
        institution=inst,
        country="TZ",
        service=service,
        payload={"id": "12345"}
    )

    mock_post.return_value = Mock(status_code=200, json=lambda: {"verified": True})

    send_verification_request(vreq.id)

    vreq.refresh_from_db()
    assert vreq.status == "VERIFIED"
    assert vreq.response_data['verified'] is True