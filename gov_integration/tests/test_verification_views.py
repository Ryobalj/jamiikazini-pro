from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, ANY

User = get_user_model()

class EntityVerificationViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("gov_integration:verify-entity")
        # the view requires authentication (gov services are not public)
        self.user = User.objects.create_user(
            email="verifier@example.com", password="pass1234",
            full_name="Verifier", role="CLIENT",
        )
        self.client.force_authenticate(user=self.user)

    def test_invalid_payload_returns_400(self):
        # Missing required fields
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("country_code", response.data)

    @patch("gov_integration.views.verification_views.verify_entity")
    def test_valid_request_returns_200_and_calls_verification(self, mock_verify_entity):
        mock_verify_entity.return_value = {
            "status": "success",
            "message": "Verified successfully",
            "data": {"some": "data"}
        }

        payload = {
            "country_code": "tz",
            "authority_code": "nida",
            "payload": {
                "national_id_number": "1234567890"
            }
        }

        response = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        mock_verify_entity.assert_called_once_with(
            country_code="tz",
            authority_code="nida",
            payload={"national_id_number": "1234567890"},
            user=ANY
        )