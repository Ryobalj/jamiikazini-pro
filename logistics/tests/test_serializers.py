# logistics/tests/test_serializers.py

from django.test import TestCase
from accounts.models import User
from kiini.models import Institution
from logistics.models import TransportProvider
from logistics.serializers.transport_provider_serializer import TransportProviderSerializer

class TransportProviderSerializerTest(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Inst 1")
        self.user = User.objects.create_user(
            email='tp@example.com',
            password='pass1234',
            full_name='TP Name',
            role='TRANSPORTER'
        )

    def test_serializer_valid(self):
        data = {
            'location': {'type': 'Point', 'coordinates': [35.75, -6.17]},
            'is_approved': False
        }
        serializer = TransportProviderSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=False))