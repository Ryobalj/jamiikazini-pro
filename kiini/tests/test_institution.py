# kiini/tests/test_institution.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from kiini.models.institution import Institution

User = get_user_model()

class InstitutionViewSetTest(APITestCase):
    def setUp(self):
        # Create two institutions
        self.inst1 = Institution.objects.create(name="Inst A")
        self.inst2 = Institution.objects.create(name="Inst B")

        # Create users linked to each institution
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="pass1234", institution=self.inst1
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", password="pass1234", institution=self.inst2
        )

        # Authenticate as user1 using JWT
        refresh = RefreshToken.for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_user_can_view_their_own_institution(self):
        url = reverse("kiini:institution-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]["id"]), str(self.inst1.id))

    def test_user_cannot_view_other_institutions(self):
        url = reverse("kiini:institution-list")

        # Switch to user2
        refresh = RefreshToken.for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get(url)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]["id"]), str(self.inst2.id))

    def test_unauthenticated_user_is_denied(self):
        self.client.credentials()  # Remove auth
        url = reverse("kiini:institution-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)