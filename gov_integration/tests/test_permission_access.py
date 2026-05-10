import pytest
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from kiini.models import Institution
from gov_integration.models import CountryConfig, ServiceType, VerificationRequest
from gov_integration.permissions.access import IsVerificationOwnerOrInstitutionAdmin

User = get_user_model()
factory = APIRequestFactory()

@pytest.mark.django_db
def test_owner_can_edit_verification():
    institution = Institution.objects.create(name="Alpha", domain="alpha")
    country = CountryConfig.objects.create(code="TZ", name="Tanzania", currency="TZS")
    service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)

    user = User.objects.create_user(
        email="owner@example.com",
        password="123",
        role="CLIENT",
        full_name="Owner User"
    )
    request = factory.patch("/")
    request.user = user

    vreq = VerificationRequest.objects.create(
        user=user, institution=institution, country="TZ", service=service, payload={"id": "123"}
    )

    perm = IsVerificationOwnerOrInstitutionAdmin()
    assert perm.has_object_permission(request, None, vreq)


@pytest.mark.django_db
def test_admin_can_read_verification():
    institution = Institution.objects.create(name="Alpha", domain="alpha")
    country = CountryConfig.objects.create(code="TZ", name="Tanzania", currency="TZS")
    service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)

    owner = User.objects.create_user(
        email="owner2@example.com",
        password="123",
        role="CLIENT",
        full_name="Owner User"
    )
    admin = User.objects.create_user(
        email="admin@example.com",
        password="123",
        role="INSTITUTION_ADMIN",
        full_name="Admin User"
    )

    vreq = VerificationRequest.objects.create(
        user=owner, institution=institution, country="TZ", service=service, payload={"id": "999"}
    )

    request = factory.get("/")
    request.user = admin

    perm = IsVerificationOwnerOrInstitutionAdmin()
    assert perm.has_object_permission(request, None, vreq)


@pytest.mark.django_db
def test_stranger_cannot_edit_verification():
    institution = Institution.objects.create(name="Alpha", domain="alpha")
    country = CountryConfig.objects.create(code="TZ", name="Tanzania", currency="TZS")
    service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)

    owner = User.objects.create_user(
        email="real_owner@example.com",
        password="123",
        role="CLIENT",
        full_name="Real Owner User"
    )
    stranger = User.objects.create_user(
        email="stranger@example.com",
        password="123",
        role="CLIENT",
        full_name="Stranger User"
    )

    vreq = VerificationRequest.objects.create(
        user=owner, institution=institution, country="TZ", service=service, payload={"id": "000"}
    )

    request = factory.patch("/")
    request.user = stranger

    perm = IsVerificationOwnerOrInstitutionAdmin()
    assert not perm.has_object_permission(request, None, vreq)


@pytest.mark.django_db
def test_superuser_can_do_anything():
    institution = Institution.objects.create(name="Alpha", domain="alpha")
    country = CountryConfig.objects.create(code="TZ", name="Tanzania", currency="TZS")
    service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)

    owner = User.objects.create_user(
        email="ownerx@example.com",
        password="123",
        role="CLIENT",
        full_name="Owner User"
    )
    superuser = User.objects.create_superuser(
        email="super@example.com",
        password="123",
        full_name="Superuser User"
    )

    vreq = VerificationRequest.objects.create(
        user=owner, institution=institution, country="TZ", service=service, payload={"id": "777"}
    )

    request = factory.patch("/")
    request.user = superuser

    perm = IsVerificationOwnerOrInstitutionAdmin()
    assert perm.has_object_permission(request, None, vreq)