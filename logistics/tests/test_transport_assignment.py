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
        self.user = User.objects.create_user(username="provider1", password="testpass")
        self.client.force_authenticate(user=self.user)

        self.provider = TransportProvider.objects.create(user=self.user)
        self.vehicle = Vehicle.objects.create(owner=self.user, plate_number="T123ABC")

        self.request = TransportRequest.objects.create(
            origin=Point(39.2, -6.8),
            destination=Point(39.3, -6.9),
            description="Cargo from A to B"
        )

    def test_assign_request_successfully(self):
        url = reverse("assignment-assign-request", args=[self.request.id])
        response = self.client.post(url, {"vehicle": self.vehicle.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TransportAssignment.objects.count(), 1)

    def test_prevent_duplicate_assignment(self):
        TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle
        )

        url = reverse("assignment-assign-request", args=[self.request.id])
        response = self.client.post(url, {"vehicle": self.vehicle.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already assigned", response.data["detail"].lower())

    def test_mark_in_transit(self):
        assignment = TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle
        )

        url = reverse("assignment-mark-in-transit", args=[assignment.id])
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

        url = reverse("assignment-mark-in-transit", args=[assignment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot change status", str(response.data["non_field_errors"]))

    def test_mark_completed_after_delivered(self):
        assignment = TransportAssignment.objects.create(
            transport_request=self.request,
            assigned_to=self.provider,
            vehicle=self.vehicle,
            assignment_status=TransportAssignment.STATUS_DELIVERED
        )

        url = reverse("assignment-mark-completed", args=[assignment.id])
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

        url = reverse("assignment-cancel", args=[assignment.id])
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

        url = reverse("assignment-mark-in-transit", args=[assignment.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot change status", str(response.data["non_field_errors"]))
