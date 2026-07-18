# gov_integration/tests/test_business_verification.py

import pytest
from unittest.mock import patch
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from kiini.models.institution import Institution
from businesses.models.business import Business
from gov_integration.models.verification_request import VerificationRequest
from gov_integration.helpers.verification import business_license_authority_for

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_business_license_authority_for_mapping():
    assert business_license_authority_for("TZ") == "tra_business"
    assert business_license_authority_for("tz") == "tra_business"
    assert business_license_authority_for("KE") == "brs"
    assert business_license_authority_for("RW") == "rdb"
    assert business_license_authority_for("UG") == "ursb"
    assert business_license_authority_for("BI") == "api"
    assert business_license_authority_for("SS") == "trade"
    assert business_license_authority_for(None) == "trade"


def test_verification_request_can_link_to_business():
    institution = Institution.objects.create(name="Duka Org", domain="dukaorg")
    owner = User.objects.create_user(
        email="owner@dukaorg.com", password="test123",
        full_name="Owner", role="PROVIDER", institution=institution,
    )
    business = Business.objects.create(
        name="Duka Langu", owner=owner, institution=institution,
        location=Point(39.2806, -6.8206, srid=4326),
    )
    vreq = VerificationRequest.objects.create(
        user=owner, institution=institution, business=business,
        country="TZ", payload={"business_license_number": "ABC123"},
    )
    assert vreq.business == business
    assert business.verification_requests.count() == 1


class TestBusinessVerificationRequestView:
    @pytest.fixture
    def setup(self):
        institution = Institution.objects.create(name="Duka Org", domain="dukaorg")
        owner = User.objects.create_user(
            email="owner@dukaorg.com", password="test123",
            full_name="Owner", role="PROVIDER", institution=institution,
        )
        other_user = User.objects.create_user(
            email="stranger@example.com", password="test123",
            full_name="Stranger", role="CLIENT",
        )
        business = Business.objects.create(
            name="Duka Langu", owner=owner, institution=institution,
            location=Point(39.2806, -6.8206, srid=4326),
        )
        return {"institution": institution, "owner": owner, "other_user": other_user, "business": business}

    def test_owner_can_request_verification_and_gets_verified(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        url = reverse("gov_integration:verify-business-license-request", kwargs={"business_id": setup["business"].pk})

        with patch("gov_integration.views.business_verification_views.verify_entity") as mock_verify:
            mock_verify.return_value = {"status": "success", "message": "ok", "data": {}}
            response = client.post(url, {"business_license_number": "ABC123", "country_code": "tz"}, format="json")

        assert response.status_code == 201
        assert response.data["status"] == "VERIFIED"
        setup["business"].refresh_from_db()
        assert setup["business"].is_verified is True
        assert VerificationRequest.objects.filter(business=setup["business"]).count() == 1
        mock_verify.assert_called_once_with("tz", "tra_business", {"business_license_number": "ABC123"}, user=setup["owner"])

    def test_failed_verification_does_not_mark_business_verified(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        url = reverse("gov_integration:verify-business-license-request", kwargs={"business_id": setup["business"].pk})

        with patch("gov_integration.views.business_verification_views.verify_entity") as mock_verify:
            mock_verify.return_value = {"status": "failed", "message": "not found"}
            response = client.post(url, {"business_license_number": "BADNUM"}, format="json")

        assert response.status_code == 201
        assert response.data["status"] == "FAILED"
        setup["business"].refresh_from_db()
        assert setup["business"].is_verified is False

    def test_non_owner_cannot_request_verification(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["other_user"])
        url = reverse("gov_integration:verify-business-license-request", kwargs={"business_id": setup["business"].pk})
        response = client.post(url, {"business_license_number": "ABC123"}, format="json")
        assert response.status_code == 403

    def test_unauthenticated_cannot_request_verification(self, setup):
        client = APIClient()
        url = reverse("gov_integration:verify-business-license-request", kwargs={"business_id": setup["business"].pk})
        response = client.post(url, {"business_license_number": "ABC123"}, format="json")
        assert response.status_code == 401

    def test_status_view_returns_history_for_owner(self, setup):
        VerificationRequest.objects.create(
            user=setup["owner"], institution=setup["institution"], business=setup["business"],
            country="TZ", payload={"business_license_number": "ABC123"}, status="VERIFIED",
        )
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        url = reverse("gov_integration:verify-business-status", kwargs={"business_id": setup["business"].pk})
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.data["requests"]) == 1

    def test_status_view_forbidden_for_non_owner(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["other_user"])
        url = reverse("gov_integration:verify-business-status", kwargs={"business_id": setup["business"].pk})
        response = client.get(url)
        assert response.status_code == 403


class TestOneBusinessPerLicenseNumber:
    """Leseni moja ya biashara = biashara moja tu - sawa na kizuizi cha NIN."""

    @pytest.fixture
    def two_businesses(self):
        institution = Institution.objects.create(name="Multi Org", domain="multiorg")
        owner1 = User.objects.create_user(
            email="owner1@example.com", password="test123",
            full_name="Owner One", role="PROVIDER", institution=institution,
        )
        owner2 = User.objects.create_user(
            email="owner2@example.com", password="test123",
            full_name="Owner Two", role="PROVIDER", institution=institution,
        )
        business1 = Business.objects.create(
            name="Biashara Moja", owner=owner1, institution=institution,
            location=Point(39.2806, -6.8206, srid=4326),
        )
        business2 = Business.objects.create(
            name="Biashara Mbili", owner=owner2, institution=institution,
            location=Point(39.2806, -6.8206, srid=4326),
        )
        return {"business1": business1, "business2": business2, "owner1": owner1, "owner2": owner2}

    def _verify(self, business, owner, license_number="SAMELICENSE001"):
        client = APIClient()
        client.force_authenticate(user=owner)
        url = reverse("gov_integration:verify-business-license-request", kwargs={"business_id": business.pk})
        with patch("gov_integration.views.business_verification_views.verify_entity") as mock_verify:
            mock_verify.return_value = {"status": "success", "message": "ok", "data": {}}
            return client.post(url, {"business_license_number": license_number, "country_code": "tz"}, format="json")

    def test_same_license_rejected_on_second_business(self, two_businesses):
        first = self._verify(two_businesses["business1"], two_businesses["owner1"])
        assert first.status_code == 201
        assert first.data["status"] == "VERIFIED"

        second = self._verify(two_businesses["business2"], two_businesses["owner2"])
        assert second.status_code == 400
        assert "leseni" in str(second.data).lower()

        two_businesses["business2"].refresh_from_db()
        assert two_businesses["business2"].is_verified is False
        assert two_businesses["business2"].license_number_hash is None

    def test_different_licenses_both_verify(self, two_businesses):
        first = self._verify(two_businesses["business1"], two_businesses["owner1"], "LICENSE-A")
        second = self._verify(two_businesses["business2"], two_businesses["owner2"], "LICENSE-B")
        assert first.status_code == 201 and first.data["status"] == "VERIFIED"
        assert second.status_code == 201 and second.data["status"] == "VERIFIED"

    def test_db_constraint_blocks_direct_duplicates(self):
        institution = Institution.objects.create(name="Direct Org", domain="directorg")
        owner1 = User.objects.create_user(
            email="direct1@example.com", password="test123",
            full_name="Direct One", role="PROVIDER", institution=institution,
        )
        owner2 = User.objects.create_user(
            email="direct2@example.com", password="test123",
            full_name="Direct Two", role="PROVIDER", institution=institution,
        )
        from django.db import IntegrityError, transaction
        from security.helpers.encryption import hash_data

        b1 = Business.objects.create(
            name="B1", owner=owner1, institution=institution,
            location=Point(39.2806, -6.8206, srid=4326),
            license_number_hash=hash_data("DUPTEST"),
        )
        b2 = Business.objects.create(
            name="B2", owner=owner2, institution=institution,
            location=Point(39.2806, -6.8206, srid=4326),
        )
        b2.license_number_hash = hash_data("DUPTEST")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                b2.save()
