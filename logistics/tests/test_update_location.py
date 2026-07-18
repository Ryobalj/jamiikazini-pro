# logistics/tests/test_update_location.py

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from kiini.models.institution import Institution
from logistics.models.transport_assignment import TransportAssignment
from logistics.models.transport_provider import TransportProvider
from logistics.models.transport_provider_verification import TransportProviderVerification
from logistics.models.transport_request import TransportRequest
from logistics.models.vehicle import Vehicle
from logistics.serializers.transport_request_serializers import TransportRequestAssignmentSerializer

User = get_user_model()


class UpdateLocationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        institution, _ = Institution.objects.get_or_create(name="Test Logistics Co")
        self.driver = User.objects.create_user(
            email="driver-track@example.com", password="testpass", full_name="Track Driver",
            role="TRANSPORTER", institution=institution,
        )
        TransportProviderVerification.objects.create(
            user=self.driver, institution=institution, overall_status="VERIFIED"
        )
        self.provider = TransportProvider.objects.create(user=self.driver)
        self.vehicle = Vehicle.objects.create(
            provider=self.provider, vehicle_type="canter", registration_number="T999XYZ",
        )

        from logistics.factories import BusinessFactory
        self.transport_request = TransportRequest.objects.create(
            business=BusinessFactory(),
            package_description="Cargo",
            weight_kg=10.0,
            pickup_location=Point(39.2, -6.8),
            dropoff_location=Point(37.7, -6.8),
            pickup_address_text="Dar es Salaam",
            dropoff_address_text="Morogoro",
        )
        self.assignment = TransportAssignment.objects.create(
            transport_request=self.transport_request,
            assigned_to=self.provider,
            vehicle=self.vehicle,
            assignment_status=TransportAssignment.STATUS_IN_TRANSIT,
        )

        self.other_user = User.objects.create_user(
            email="buyer-track@example.com", password="testpass", full_name="Buyer",
        )
        from businesses.models.order import Order, FulfillmentType
        self.order = Order.objects.create(
            client=self.other_user,
            business=self.transport_request.business,
            total_amount=10000,
            fulfillment_type=FulfillmentType.DELIVERY,
        )
        self.transport_request.order = self.order
        self.transport_request.save(update_fields=["order"])

        self.body = {"current_location": {"type": "Point", "coordinates": [39.25, -6.75]}}

    def test_driver_can_update_location_while_in_transit(self):
        self.client.force_authenticate(user=self.driver)
        url = reverse("logistics:assignment-update-location", args=[self.assignment.id])
        response = self.client.post(url, self.body, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assignment.refresh_from_db()
        self.assertAlmostEqual(self.assignment.current_location.x, 39.25)
        self.assertAlmostEqual(self.assignment.current_location.y, -6.75)

    def test_buyer_cannot_update_location(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse("logistics:assignment-update-location", args=[self.assignment.id])
        response = self.client.post(url, self.body, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_cannot_update_location_outside_in_transit(self):
        self.assignment.assignment_status = TransportAssignment.STATUS_ASSIGNED
        self.assignment.save(update_fields=["assignment_status"])

        self.client.force_authenticate(user=self.driver)
        url = reverse("logistics:assignment-update-location", args=[self.assignment.id])
        response = self.client.post(url, self.body, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transport_request_assignment_serializer_exposes_current_location(self):
        self.assignment.current_location = Point(39.25, -6.75, srid=4326)
        self.assignment.save(update_fields=["current_location"])

        data = TransportRequestAssignmentSerializer(self.assignment).data
        self.assertIn("current_location", data)
        self.assertEqual(data["current_location"]["type"], "Point")
        self.assertAlmostEqual(data["current_location"]["coordinates"][0], 39.25)
        self.assertAlmostEqual(data["current_location"]["coordinates"][1], -6.75)
