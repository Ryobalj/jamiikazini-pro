# kiini/tests/test_department.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from kiini.models.institution import Institution
from kiini.models.department import Department

User = get_user_model()

class DepartmentAPITestCase(APITestCase):
    def setUp(self):
        # Create two institutions
        self.inst1 = Institution.objects.create(name="Institution A", domain="insta")
        self.inst2 = Institution.objects.create(name="Institution B", domain="instb")

        # Create users
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="pass1234", institution=self.inst1, role="INSTITUTION_ADMIN"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", password="pass1234", institution=self.inst2, role="INSTITUTION_ADMIN"
        )

        # Create departments
        self.dept1 = Department.objects.create(
            institution=self.inst1, name="HR", description="HR Department"
        )
        self.dept2 = Department.objects.create(
            institution=self.inst2, name="Finance", description="Finance Dept"
        )

        # Authenticate as user1
        self.authenticate(self.user1)

    def authenticate(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")

    def test_list_departments(self):
        url = reverse("kiini:institution-departments-list", args=[self.inst1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "HR")

    def test_create_department(self):
        url = reverse("kiini:institution-departments-list", args=[self.inst1.id])
        data = {"name": "IT", "description": "IT Department", "is_active": True}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "IT")

    def test_update_department(self):
        url = reverse("kiini:institution-departments-detail", args=[self.inst1.id, self.dept1.id])
        data = {"name": "Human Resources"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Human Resources")

    def test_user_cannot_access_other_institution_department(self):
        self.authenticate(self.user2)
        url = reverse("kiini:institution-departments-detail", args=[self.inst1.id, self.dept1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)