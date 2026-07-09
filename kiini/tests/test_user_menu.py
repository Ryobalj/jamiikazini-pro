from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from kiini.models.institution import Institution


User = get_user_model()

class UserMenuTests(APITestCase):

    def setUp(self):
        """Setup test user and institution."""
        self.institution = Institution.objects.create(
            name="Test Institution",
            domain="testdomain"
        )
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass1234",
            full_name="Test User",
        )
        # Assign institution
        # 'roles' ni property inayotokana na 'role' - weka 'role'
        self.user.institution = self.institution
        self.user.role = "CLIENT"
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_user_menu_without_roles(self):
        """Check menu when user has no roles."""
        self.user.role = ""
        self.user.save()
        url = reverse("kiini:user-menu")  # ✅ New namespace
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(isinstance(response.data, list), True)

    def test_user_menu_with_valid_role(self):
        """Check menu when user has a valid role."""
        self.user.role = "CLIENT"
        self.user.save()
        url = reverse("kiini:user-menu")  # ✅ New namespace
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(isinstance(response.data, list), True)

    def test_user_menu_with_domain_check(self):
        """Check menu when user has matching domain."""
        self.user.role = "INSTITUTION_ADMIN"
        self.user.save()
        url = reverse("kiini:user-menu")  # ✅ New namespace
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in response.data:
            if item.get("domain"):
                self.assertEqual(item["domain"], self.institution.domain)

    def test_user_menu_not_authenticated(self):
        """Check menu when user is not logged in."""
        self.client.logout()
        url = reverse("kiini:user-menu")  # ✅ New namespace
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)