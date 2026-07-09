# logistics/tests/test_models.py

from django.test import TestCase
from accounts.models import User
from kiini.models import Institution
from logistics.models import TransportProvider, TransportProviderVerification

class TransportProviderModelTest(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Test Institution")
        self.user = User.objects.create_user(
            email='driver@example.com',
            password='pass1234',
            full_name='Driver Test',
            role='TRANSPORTER'
        )

    def test_create_transport_provider(self):
        tp = TransportProvider.objects.create(user=self.user, institution=self.institution)
        self.assertEqual(tp.user.email, 'driver@example.com')
        self.assertFalse(tp.is_approved)

class TransportProviderVerificationModelTest(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Test Institution")
        self.user = User.objects.create_user(
            email='verifier@example.com',
            password='pass1234',
            full_name='Verifier Test',
            role='TRANSPORTER'
        )

    def test_create_verification_entry(self):
        tpv = TransportProviderVerification.objects.create(
            user=self.user,
            institution=self.institution,
            overall_status="PENDING"
        )
        self.assertEqual(tpv.overall_status, "PENDING")