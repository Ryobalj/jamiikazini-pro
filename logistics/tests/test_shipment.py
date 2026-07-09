# logistics/tests/test_shipment.py
#
# Rewritten against the current models: Product belongs to a Business (not an
# owner user), Shipment has no preferred_transport_modes field, TransportProvider
# is user+institution based (no name/slug), and subdomain URLs come from
# Institution.domain.

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from logistics.models import Shipment, ShipmentStatus, TransportProvider
from logistics.factories import ProductFactory


User = get_user_model()


class ShipmentModelTest(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(email='sender@example.com', password='pass1234')
        self.receiver = User.objects.create_user(email='receiver@example.com', password='pass1234')
        self.product = ProductFactory(name='Test Product', price=100)

        self.shipment = Shipment.objects.create(
            product=self.product,
            sender=self.sender,
            receiver=self.receiver,
            status=ShipmentStatus.PENDING,
            tax_paid=True,
            transport_fee=100,
            jamiikazini_commission=10,
            total_cost=110
        )

    def test_shipment_string(self):
        self.assertEqual(str(self.shipment), f"Shipment #{self.shipment.id} from {self.sender} to {self.receiver}")

    def test_is_fully_paid_true(self):
        self.assertTrue(self.shipment.is_fully_paid())

    def test_is_fully_paid_false_if_tax_unpaid(self):
        self.shipment.tax_paid = False
        self.shipment.save()
        self.assertFalse(self.shipment.is_fully_paid())

    def test_add_transport_provider(self):
        provider_user = User.objects.create_user(email='provider@example.com', password='pass1234')
        provider = TransportProvider.objects.create(user=provider_user)
        self.shipment.transport_providers.add(provider)
        self.assertIn(provider, self.shipment.transport_providers.all())


class ShipmentAPITest(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(email='sender@example.com', password='pass1234')
        self.receiver = User.objects.create_user(email='receiver@example.com', password='pass1234')
        self.client.force_authenticate(user=self.sender)

        self.product = ProductFactory(name='API Product', price=100)

        self.shipment = Shipment.objects.create(
            product=self.product,
            sender=self.sender,
            receiver=self.receiver,
            status=ShipmentStatus.PENDING,
            tax_paid=False,
            transport_fee=50,
            jamiikazini_commission=5,
            total_cost=55
        )

    def test_list_shipments(self):
        url = reverse('logistics:shipment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_shipment(self):
        url = reverse('logistics:shipment-detail', args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.shipment.id)

    def test_create_shipment(self):
        url = reverse('logistics:shipment-list')
        data = {
            'product_id': self.product.id,
            'receiver_id': self.receiver.id,
            'transport_fee': 120,
            'jamiikazini_commission': 10,
            'total_cost': 130,
            'tax_paid': True,
            'status': ShipmentStatus.PENDING
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_update_shipment_status(self):
        url = reverse('logistics:shipment-detail', args=[self.shipment.id])
        data = {'status': ShipmentStatus.IN_TRANSIT}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], ShipmentStatus.IN_TRANSIT)

    def test_delete_shipment(self):
        url = reverse('logistics:shipment-detail', args=[self.shipment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ShipmentURLActionsTests(APITestCase):
    """Subdomain URL actions build links from Institution.domain."""

    def setUp(self):
        from kiini.models import Institution

        self.sender_institution = Institution.objects.create(
            name="SenderInst", domain="senderinst.jamiikazini.com")
        self.receiver_institution = Institution.objects.create(
            name="ReceiverInst", domain="receiverinst.jamiikazini.com")
        self.provider_institution = Institution.objects.create(
            name="TransProvider", domain="transprovider.jamiikazini.com")

        self.sender_user = User.objects.create_user(
            email='sender@example.com', password='pass123',
            institution=self.sender_institution)
        self.receiver_user = User.objects.create_user(
            email='receiver@example.com', password='pass123',
            institution=self.receiver_institution)
        provider_user = User.objects.create_user(
            email='provider@example.com', password='pass123',
            institution=self.provider_institution)

        self.transport_provider = TransportProvider.objects.create(
            user=provider_user, institution=self.provider_institution)

        self.shipment = Shipment.objects.create(
            sender=self.sender_user,
            receiver=self.receiver_user,
            product=ProductFactory(),
            transport_fee=100,
            jamiikazini_commission=10,
            status=ShipmentStatus.PENDING,
            tax_paid=False,
            total_cost=110,
        )
        self.shipment.transport_providers.add(self.transport_provider)

    def test_sender_url_action(self):
        self.client.force_authenticate(user=self.sender_user)
        url = reverse('logistics:shipment-detail', args=[self.shipment.id]) + 'sender_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sender_url', response.data)
        self.assertTrue(response.data['sender_url'].startswith('https://senderinst.'))

    def test_receiver_url_action(self):
        self.client.force_authenticate(user=self.receiver_user)
        url = reverse('logistics:shipment-detail', args=[self.shipment.id]) + 'receiver_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('receiver_url', response.data)
        self.assertTrue(response.data['receiver_url'].startswith('https://receiverinst.'))

    def test_transport_provider_url_action(self):
        self.client.force_authenticate(user=self.sender_user)
        url = reverse('logistics:shipment-detail', args=[self.shipment.id]) + 'transport_provider_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transport_provider_url', response.data)
        self.assertTrue(response.data['transport_provider_url'].startswith('https://transprovider.'))

    def test_sender_url_no_institution(self):
        self.sender_user.institution = None
        self.sender_user.save()
        self.client.force_authenticate(user=self.sender_user)
        url = reverse('logistics:shipment-detail', args=[self.shipment.id]) + 'sender_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_receiver_url_no_institution(self):
        self.receiver_user.institution = None
        self.receiver_user.save()
        self.client.force_authenticate(user=self.receiver_user)
        url = reverse('logistics:shipment-detail', args=[self.shipment.id]) + 'receiver_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transport_provider_url_no_domain(self):
        self.provider_institution.domain = None
        self.provider_institution.save()
        self.client.force_authenticate(user=self.sender_user)
        url = reverse('logistics:shipment-detail', args=[self.shipment.id]) + 'transport_provider_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
