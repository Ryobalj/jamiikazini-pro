from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from kiini.models.institution import Institution
from kiini.models.department import Department
from kiini.models.staff import StaffProfile

User = get_user_model()


class KiiniURLTests(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Sample Institution")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass1234",
            institution=self.institution,
            role="INSTITUTION_ADMIN"
        )
        self.department = Department.objects.create(
            institution=self.institution,
            name="ICT",
            description="ICT Department"
        )
        self.staff = StaffProfile.objects.create(
            institution=self.institution,
            user=self.user,
            position="Manager",
            phone="0761234567",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_institution_list_url(self):
        url = reverse("kiini:institution-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nested_department_list_url(self):
        url = reverse("kiini:institution-departments-list", kwargs={"institution_pk": self.institution.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nested_department_detail_url(self):
        url = reverse("kiini:institution-departments-detail", kwargs={
            "institution_pk": self.institution.pk,
            "pk": self.department.pk
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nested_staff_list_url(self):
        url = reverse("kiini:institution-staffprofiles-list", kwargs={"institution_pk": self.institution.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nested_staff_detail_url(self):
        url = reverse("kiini:institution-staffprofiles-detail", kwargs={
            "institution_pk": self.institution.pk,
            "pk": self.staff.pk
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_menu_authenticated(self):
        """Hakikisha user-menu inapatikana kwa mtumiaji aliye-login"""
        url = reverse("kiini:user-menu")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_menu_unauthenticated(self):
        """Hakikisha user-menu inakataa mtumiaji asiyelogin"""
        self.client.credentials()  # Toa JWT
        url = reverse("kiini:user-menu")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_access(self):
        """Hakikisha endpoints haziruhusu bila JWT"""
        self.client.credentials()  # Toa JWT
        url = reverse("kiini:institution-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)