# logistics/tests/test_transport_provider_views.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from accounts.models import User
from core.models import Institution
from logistics.models import TransportProvider
from rest_framework_simplejwt.tokens import RefreshToken

class TransportProviderViewSetTest(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Inst View")
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass',
            full_name='User View',
            role='TRANSPORTER'
        )
        self.user.institution = self.institution
        self.user.save()

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_create_transport_provider(self):
        url = reverse('transport-provider-list')
        data = {
            'location': 'Mwanza',
            'is_approved': False
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['location'], 'Mwanza')

    def test_list_transport_providers(self):
        TransportProvider.objects.create(
            user=self.user,
            institution=self.institution,
            location='Mbeya'
        )
        url = reverse('transport-provider-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)