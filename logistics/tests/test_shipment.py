# logistics/tests/test_shipment.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from logistics.models import Shipment, ShipmentStatus, TransportProvider
from businesses.models.product import Product
from kiini.models import Institution


User = get_user_model()


class ShipmentModelTest(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(email='sender@example.com', password='pass1234')
        self.receiver = User.objects.create_user(email='receiver@example.com', password='pass1234')
        self.product = Product.objects.create(name='Test Product', price=100, owner=self.sender)

        self.shipment = Shipment.objects.create(
            product=self.product,
            sender=self.sender,
            receiver=self.receiver,
            preferred_transport_modes=['TRUCK'],
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
        provider = TransportProvider.objects.create(name="Provider X")
        self.shipment.transport_providers.add(provider)
        self.assertIn(provider, self.shipment.transport_providers.all())


class ShipmentAPITest(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(email='sender@example.com', password='pass1234')
        self.receiver = User.objects.create_user(email='receiver@example.com', password='pass1234')
        self.client.force_authenticate(user=self.sender)

        self.product = Product.objects.create(name='API Product', price=100, owner=self.sender)

        self.shipment = Shipment.objects.create(
            product=self.product,
            sender=self.sender,
            receiver=self.receiver,
            preferred_transport_modes=['BIKE'],
            status=ShipmentStatus.PENDING,
            tax_paid=False,
            transport_fee=50,
            jamiikazini_commission=5,
            total_cost=55
        )

    def test_list_shipments(self):
        url = reverse('shipment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_shipment(self):
        url = reverse('shipment-detail', args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.shipment.id)

    def test_create_shipment(self):
        url = reverse('shipment-list')
        data = {
            'product': self.product.id,
            'sender': self.sender.id,
            'receiver': self.receiver.id,
            'preferred_transport_modes': ['TRUCK', 'AIR'],
            'transport_fee': 120,
            'jamiikazini_commission': 10,
            'total_cost': 130,
            'tax_paid': True,
            'status': ShipmentStatus.PENDING
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product'], self.product.id)

    def test_update_shipment_status(self):
        url = reverse('shipment-detail', args=[self.shipment.id])
        data = {'status': ShipmentStatus.IN_TRANSIT}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], ShipmentStatus.IN_TRANSIT)

    def test_delete_shipment(self):
        url = reverse('shipment-detail', args=[self.shipment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ShipmentURLActionsTests(APITestCase):

    def setUp(self):
        # Create users
        self.sender_user = User.objects.create_user(username='sender', password='pass123')
        self.receiver_user = User.objects.create_user(username='receiver', password='pass123')

        # Create Institutions and assign to users
        self.sender_institution = Institution.objects.create(name="SenderInst", slug="senderinst")
        self.receiver_institution = Institution.objects.create(name="ReceiverInst", slug="receiverinst")

        # Assume User has a FK to institution or some link
        self.sender_user.institution = self.sender_institution
        self.sender_user.save()
        self.receiver_user.institution = self.receiver_institution
        self.receiver_user.save()

        # Create transport provider with slug
        self.transport_provider = TransportProvider.objects.create(name="TransProvider", slug="transprovider")

        # Create shipment linked to sender, receiver and transport provider
        self.shipment = Shipment.objects.create(
            sender=self.sender_user,
            receiver=self.receiver_user,
            product_id=1,  # Adjust as per your actual Product FK requirements
            transport_fee=100,
            jamiikazini_commission=10,
            status='pending',
            tax_paid=False,
            total_cost=110,
        )
        self.shipment.transport_providers.add(self.transport_provider)

    def test_sender_url_action(self):
        self.client.login(username='sender', password='pass123')
        url = reverse('shipment-detail', args=[self.shipment.id]) + 'sender_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sender_url', response.data)
        self.assertTrue(response.data['sender_url'].startswith('https://senderinst.'))

    def test_receiver_url_action(self):
        self.client.login(username='receiver', password='pass123')
        url = reverse('shipment-detail', args=[self.shipment.id]) + 'receiver_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('receiver_url', response.data)
        self.assertTrue(response.data['receiver_url'].startswith('https://receiverinst.'))

    def test_transport_provider_url_action(self):
        # Login as sender or any user with permission
        self.client.login(username='sender', password='pass123')
        url = reverse('shipment-detail', args=[self.shipment.id]) + 'transport_provider_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transport_provider_url', response.data)
        self.assertTrue(response.data['transport_provider_url'].startswith('https://transprovider.'))

    def test_sender_url_no_institution(self):
        # Remove institution from sender user
        self.sender_user.institution = None
        self.sender_user.save()
        self.client.login(username='sender', password='pass123')
        url = reverse('shipment-detail', args=[self.shipment.id]) + 'sender_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_receiver_url_no_institution(self):
        self.receiver_user.institution = None
        self.receiver_user.save()
        self.client.login(username='receiver', password='pass123')
        url = reverse('shipment-detail', args=[self.shipment.id]) + 'receiver_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transport_provider_url_no_slug(self):
        self.transport_provider.slug = None
        self.transport_provider.save()
        self.client.login(username='sender', password='pass123')
        url = reverse('shipment-detail', args=[self.shipment.id]) + 'transport_provider_url/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)