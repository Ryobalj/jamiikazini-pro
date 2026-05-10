import pytest
from gov_integration.models import CountryConfig, ServiceType, VerificationRequest
from kiini.models import Institution
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_create_country_and_service_type():
    country = CountryConfig.objects.create(code="KE", name="Kenya", currency="KES")
    service = ServiceType.objects.create(name="KRA", code="KRA", country=country)

    assert country.code == "KE"
    assert service.country == country


@pytest.mark.django_db
def test_create_verification_request():
    country = CountryConfig.objects.create(code="TZ", name="Tanzania", currency="TZS")
    service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)
    institution = Institution.objects.create(name="Inst", domain="inst")

    user = User.objects.create_user(
        email="client@example.com",
        password="test",
        role="CLIENT",
        full_name="Client User"
    )

    vreq = VerificationRequest.objects.create(
        user=user,
        institution=institution,
        country="TZ",
        service=service,
        payload={"id": "123456"}
    )

    assert vreq.status == "PENDING"
    assert vreq.payload['id'] == "123456"