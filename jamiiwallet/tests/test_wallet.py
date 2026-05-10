# jamiiwallet/tests/test_wallet.py

from django.test import override_settings
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from jamiiwallet.models.wallet import Wallet
from jamiiwallet.serializers.wallet_serializer import WalletSerializer
from django.urls import reverse

User = get_user_model()

@override_settings(
    MIDDLEWARE=[mw for mw in settings.MIDDLEWARE if 'InstitutionMiddleware' not in mw],
    ALLOWED_HOSTS=['testserver']
)
class WalletTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123'
        )
        self.client.force_authenticate(user=self.user)

    def test_wallet_created_on_user_creation(self):
        self.assertTrue(Wallet.objects.filter(user=self.user).exists())

    def test_wallet_serializer_data(self):
        wallet = self.user.wallet
        serializer = WalletSerializer(wallet)
        self.assertEqual(serializer.data['user'], self.user.id)  # if user is int
        self.assertIn('balance', serializer.data)
        self.assertIn('currency', serializer.data)

    def test_unauthorized_wallet_access(self):
        self.client.logout()
        url = reverse('jamiiwallet:wallet-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)