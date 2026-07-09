# logistics/tests/test_transport_assignment.py

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.gis.geos import Point

from logistics.models.transport_assignment import TransportAssignment
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle


User = get_user_model()

class TransportAssignmentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create user and authenticate
        self.user = User.objects.create_user(email="provider1@example.com", password="testpass", full_name="Provider One", role="TRANSPORTER")
        self.client.force_authenticate(user=self.user)

        self.provider = TransportProvider.objects.create(user=self.user)
        self.vehicle = Vehicle.objects.create(
            provider=self.provider,
            vehicle_type="canter",
            registration_number="T123ABC",
        )

        from logistics.factories import BusinessFactory
        self.request = TransportRequest.objects.create(
            business=BusinessFactory(),
            package_description="Cargo from A to B",
            weight_kg=10.0,
            pickup_location=Point(39.2, -6.8),
            dropoff_location=Point(37.7, -6.8),
            pickup_address_text="Dar es Salaam",
            dropoff_address_text="Morogoro",
        )

    def test_assign_request_successfully(self):
        url = reverse("logistics:assignment-assign-request", args=[self.request.id])
        response = self.client.post(url, {"vehicle": self.vehicle.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TransportAssignment.objects.count(), 1)

    def test_prevent_duplicate_assignment(self):
        TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle
        )

        url = reverse("logistics:assignment-assign-request", args=[self.request.id])
        response = self.client.post(url, {"vehicle": self.vehicle.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already assigned", response.data["detail"].lower())

    def test_mark_in_transit(self):
        assignment = TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle
        )

        url = reverse("logistics:assignment-mark-in-transit", args=[assignment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertEqual(assignment.assignment_status, TransportAssignment.STATUS_IN_TRANSIT)

    def test_invalid_status_transition(self):
        assignment = TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle,
            assignment_status=TransportAssignment.STATUS_COMPLETED
        )

        url = reverse("logistics:assignment-mark-in-transit", args=[assignment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot change status", str(response.data))

    def test_mark_completed_after_delivered(self):
        assignment = TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle,
            assignment_status=TransportAssignment.STATUS_DELIVERED
        )

        url = reverse("logistics:assignment-mark-completed", args=[assignment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertEqual(assignment.assignment_status, TransportAssignment.STATUS_COMPLETED)

    def test_cancel_assignment(self):
        assignment = TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle
        )

        url = reverse("logistics:assignment-cancel", args=[assignment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertEqual(assignment.assignment_status, TransportAssignment.STATUS_CANCELLED)

    def test_serializer_status_validation(self):
        assignment = TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle,
            assignment_status=TransportAssignment.STATUS_DELIVERED
        )

        url = reverse("logistics:assignment-mark-in-transit", args=[assignment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot change status", str(response.data))
