# kiini/tests/test_staffprofile.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from kiini.models.institution import Institution
from kiini.models.staff import StaffProfile

User = get_user_model()

class StaffProfileAPITestCase(APITestCase):

    def setUp(self):
        # Create two institutions
        self.inst1 = Institution.objects.create(name="Institution A", domain="insta")
        self.inst2 = Institution.objects.create(name="Institution B", domain="instb")

        # Create users
        self.admin1 = User.objects.create_user(
            email="admin1@example.com", password="admin1234",
            institution=self.inst1, role="INSTITUTION_ADMIN"
        )

        self.admin2 = User.objects.create_user(
            email="admin2@example.com", password="admin1234",
            institution=self.inst2, role="INSTITUTION_ADMIN"
        )

        self.staff1 = StaffProfile.objects.create(
            institution=self.inst1,
            user=self.admin1,
            title="Head Teacher",
            department=None
        )

        # Auth tokens
        self.admin1_token = str(RefreshToken.for_user(self.admin1).access_token)
        self.admin2_token = str(RefreshToken.for_user(self.admin2).access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin1_token}")

    def test_list_staff_profiles(self):
        url = reverse("kiini:institution-staffprofiles-list", args=[self.inst1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"], self.admin1.id)

    def test_create_staff_profile(self):
        new_user = User.objects.create_user(
            email="staffx@example.com", password="staffpass",
            institution=self.inst1, role="STAFF"
        )
        url = reverse("kiini:institution-staffprofiles-list", args=[self.inst1.id])
        data = {
            "user": new_user.id,
            "title": "Deputy",
            "department": None
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], new_user.id)

    def test_retrieve_staff_profile(self):
        url = reverse("kiini:institution-staffprofiles-detail", args=[self.inst1.id, self.staff1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.staff1.id)

    def test_user_cannot_access_other_institution_staff_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin2_token}")
        url = reverse("kiini:institution-staffprofiles-detail", args=[self.inst1.id, self.staff1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_access(self):
        self.client.credentials()
        url = reverse("kiini:institution-staffprofiles-list", args=[self.inst1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
