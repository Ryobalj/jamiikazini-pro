import unittest
from unittest.mock import patch, MagicMock
from gov_integration.helpers.verification import (
    get_gov_api_config,
    verify_entity,
    mock_response
)


class TestGovVerification(unittest.TestCase):

    def test_get_gov_api_config_found(self):
        config = get_gov_api_config("tz", "nida")
        self.assertIsNotNone(config)
        self.assertIn("api_url", config)
        self.assertIn("api_key", config)

    def test_get_gov_api_config_not_found(self):
        config = get_gov_api_config("xx", "unknown")
        self.assertIsNone(config)

    @patch("gov_integration.helpers.verification.requests.post")
    def test_verify_entity_real_api_success(self, mock_post):
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = {"verified": True}
        mock_post.return_value = mock_response_obj

        payload = {"national_id_number": "12345678"}
        result = verify_entity("tz", "nida", payload)
        self.assertEqual(result, {"verified": True})

    @patch("gov_integration.helpers.verification.requests.post")
    def test_verify_entity_api_failure_uses_mock(self, mock_post):
        mock_post.side_effect = Exception("API Down")

        payload = {"license_number": "A12345"}
        result = verify_entity("tz", "tra_driver", payload)
        self.assertEqual(result["status"], "success")
        self.assertIn("Driver License verification", result["message"])
        self.assertIn("holder_name", result["data"])

    def test_mock_response_nida(self):
        payload = {"national_id_number": "1234567890"}
        response = mock_response("nida", payload)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["full_name"], "John Doe")

    def test_mock_response_unknown(self):
        payload = {"some": "data"}
        response = mock_response("unknown", payload)
        self.assertEqual(response["status"], "mock_success")
        self.assertEqual(response["data"], payload)

    def test_mock_response_transport(self):
        payload = {"latra_license_number": "LAT1234"}
        response = mock_response("latra", payload)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["operator_name"], "Express Transport Ltd")


if __name__ == "__main__":
    unittest.main()