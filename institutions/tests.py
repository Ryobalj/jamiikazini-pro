from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from kiini.models.institution import Institution

User = get_user_model()


class MyInstitutionsListTest(APITestCase):
    def setUp(self):
        self.owned = Institution.objects.create(name="Owned Institution")
        self.member_of = Institution.objects.create(name="Member Institution")
        self.other = Institution.objects.create(name="Unrelated Institution")

        self.owner = User.objects.create_user(email="owner@example.com", password="pass1234")
        self.owned.owner = self.owner
        self.owned.save(update_fields=["owner"])

        # Staff member (not owner) linked via User.institution
        self.staff = User.objects.create_user(
            email="staff@example.com", password="pass1234", institution=self.member_of,
        )

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

    def test_owner_sees_owned_institution(self):
        self._auth(self.owner)
        response = self.client.get(reverse("my-institutions"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in response.data}
        self.assertIn(str(self.owned.id), ids)
        self.assertNotIn(str(self.other.id), ids)

    def test_staff_member_sees_their_institution_without_owning_it(self):
        self._auth(self.staff)
        response = self.client.get(reverse("my-institutions"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in response.data}
        self.assertIn(str(self.member_of.id), ids)
        self.assertNotIn(str(self.other.id), ids)

    def test_unauthenticated_user_is_denied(self):
        response = self.client.get(reverse("my-institutions"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
