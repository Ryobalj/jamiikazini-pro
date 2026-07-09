# logistics/tests/test_transport_verification_views.py

from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from accounts.models import User
from kiini.models import Institution
from logistics.models import TransportProviderVerification
from unittest.mock import patch
import logistics.views.transport_provider_verification_views  # noqa: F401 - needed so @patch can resolve the module

class TransportProviderVerificationTests(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Test Logistics Co")
        self.transporter = User.objects.create_user(
            email="john@logistics.com",
            password="1234",
            role="TRANSPORTER",
            full_name="John Transporter",
            institution=self.institution
        )
        self.admin = User.objects.create_user(
            email="admin@logistics.com",
            password="1234",
            role="INSTITUTION_ADMIN",
            full_name="Admin User",
            institution=self.institution
        )
        self.verify_url = reverse("logistics:transport-verification-verify-all")
        self.client = APIClient()

    @patch("logistics.views.transport_provider_verification_views.verify_entity")
    def test_verify_all_for_transporter(self, mock_verify):
        # request_id must be a real VerificationRequest pk (FK on the tpv record)
        from gov_integration.models import VerificationRequest, CountryConfig, ServiceType
        country = CountryConfig.objects.create(code="TZ", name="Tanzania", currency="TZS")
        service = ServiceType.objects.create(name="NIDA", code="NIDA", country=country)
        vr = VerificationRequest.objects.create(
            user=self.transporter,
            institution=self.institution,
            country="TZ",
            service=service,
            payload={"national_id_number": "12345678"},
        )
        mock_verify.return_value = {
            "status": "success",
            "data": {"request_id": vr.id},
        }
        self.client.force_authenticate(user=self.transporter)
        data = {
            "country_code": "tz",
            "national_id_number": "12345678",
            "driver_license_number": "D1234",
            "business_license_number": "B5678",
            "latra_license_number": "L9988"
        }
        response = self.client.post(self.verify_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_verify.call_count, 4)
        tpv = TransportProviderVerification.objects.get(user=self.transporter)
        self.assertIsNotNone(tpv.nida_verification_id)
        self.assertEqual(tpv.institution, self.institution)

    def test_verify_all_requires_authentication(self):
        response = self.client.post(self.verify_url, {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_viewset_queryset_filtering(self):
        tpv = TransportProviderVerification.objects.create(user=self.transporter, institution=self.institution)
        url = reverse("logistics:transport-verification-list")

        # Transporter should only see their own record
        self.client.force_authenticate(user=self.transporter)
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

        # Institution admin should see all records under same institution
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

        # Client should see nothing
        outsider = User.objects.create_user(
            email="client@example.com",
            password="1234",
            role="CLIENT",
            full_name="Client X"
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)