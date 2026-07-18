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
        # _save_verification_result now creates its own VerificationRequest row from
        # the response itself, rather than trusting an inbound request_id - so the
        # mock only needs to report a successful status.
        mock_verify.return_value = {
            "status": "success",
            "data": {"full_name": "John Doe"},
        }
        self.client.force_authenticate(user=self.transporter)
        data = {
            "country_code": "tz",
            "national_id_number": "12345678",
            "driver_license_number": "D1234",
            "vehicle_license_number": "V5678",
            "latra_license_number": "L9988"
        }
        response = self.client.post(self.verify_url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_verify.call_count, 4)
        tpv = TransportProviderVerification.objects.get(user=self.transporter)
        self.assertIsNotNone(tpv.nida_verification_id)
        self.assertIsNotNone(tpv.driving_license_verification_id)
        self.assertIsNotNone(tpv.vehicle_license_verification_id)
        self.assertIsNotNone(tpv.latra_permit_verification_id)
        self.assertEqual(tpv.overall_status, "VERIFIED")
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


class OneDriverPerLicenseNumberTests(APITestCase):
    """Leseni moja ya udereva = dereva mmoja tu - sawa na kizuizi cha NIN."""

    def setUp(self):
        self.institution = Institution.objects.create(name="Dual Driver Co")
        self.driver1 = User.objects.create_user(
            email="driver1@logistics.com", password="1234",
            role="TRANSPORTER", full_name="Driver One", institution=self.institution,
        )
        self.driver2 = User.objects.create_user(
            email="driver2@logistics.com", password="1234",
            role="TRANSPORTER", full_name="Driver Two", institution=self.institution,
        )
        self.verify_url = reverse("logistics:transport-verification-verify-all")
        self.client = APIClient()

    @patch("logistics.views.transport_provider_verification_views.verify_entity")
    def test_same_driver_license_rejected_on_second_driver(self, mock_verify):
        mock_verify.return_value = {"status": "success", "data": {}}

        self.client.force_authenticate(user=self.driver1)
        first = self.client.post(self.verify_url, {
            "country_code": "tz", "driver_license_number": "SAMEDL001",
        }, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["driver_license"]["status"], "success")

        self.client.force_authenticate(user=self.driver2)
        second = self.client.post(self.verify_url, {
            "country_code": "tz", "driver_license_number": "SAMEDL001",
        }, format="json")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["driver_license"]["status"], "failed")

        tpv2 = TransportProviderVerification.objects.filter(user=self.driver2).first()
        self.assertIsNone(tpv2)

    @patch("logistics.views.transport_provider_verification_views.verify_entity")
    def test_different_driver_licenses_both_verify(self, mock_verify):
        mock_verify.return_value = {"status": "success", "data": {}}

        self.client.force_authenticate(user=self.driver1)
        first = self.client.post(self.verify_url, {
            "country_code": "tz", "driver_license_number": "DL-A",
        }, format="json")
        self.client.force_authenticate(user=self.driver2)
        second = self.client.post(self.verify_url, {
            "country_code": "tz", "driver_license_number": "DL-B",
        }, format="json")

        self.assertEqual(first.data["driver_license"]["status"], "success")
        self.assertEqual(second.data["driver_license"]["status"], "success")

    @patch("logistics.views.transport_provider_verification_views.verify_entity")
    def test_same_driver_can_reverify_own_license(self, mock_verify):
        mock_verify.return_value = {"status": "success", "data": {}}
        self.client.force_authenticate(user=self.driver1)

        first = self.client.post(self.verify_url, {
            "country_code": "tz", "driver_license_number": "OWNDL001",
        }, format="json")
        second = self.client.post(self.verify_url, {
            "country_code": "tz", "driver_license_number": "OWNDL001",
        }, format="json")

        self.assertEqual(first.data["driver_license"]["status"], "success")
        self.assertEqual(second.data["driver_license"]["status"], "success")