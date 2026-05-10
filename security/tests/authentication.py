from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch

User = get_user_model()

class UnifiedLoginViewTests(APITestCase):
    def setUp(self):
        self.login_url = reverse('unified-login')  # Hakikisha hii ipo kwenye urls.py
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='StrongPass123',
            full_name='Test User',
            role='CLIENT'
        )

    @patch('security.views.auth.BaseLoginLogger.log_success')
    def test_successful_login(self, mock_log_success):
        response = self.client.post(self.login_url, {
            "email": self.user.email,
            "password": "StrongPass123"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        mock_log_success.assert_called_once()

    @patch('security.views.auth.BaseLoginLogger.log_failure')
    def test_login_with_invalid_credentials(self, mock_log_failure):
        response = self.client.post(self.login_url, {
            "email": self.user.email,
            "password": "WrongPass"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_log_failure.assert_called_once()

    @patch('security.views.auth.BaseLoginLogger.log_success')
    def test_successful_login_with_cookies(self, mock_log_success):
        response = self.client.post(f"{self.login_url}?use_cookies=true", {
            "email": self.user.email,
            "password": "StrongPass123"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)
        mock_log_success.assert_called_once()
