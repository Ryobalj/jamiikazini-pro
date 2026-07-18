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

    def test_plain_client_menu_has_no_business_or_driver_dashboard(self):
        url = reverse("kiini:user-menu")
        response = self.client.get(url)
        apps = {item["app"] for item in response.data}
        self.assertIn("wallet", apps)
        self.assertIn("cart", apps)
        self.assertIn("orders", apps)
        self.assertIn("chat", apps)
        business_item = next(item for item in response.data if item["app"] == "business")
        self.assertEqual(business_item["i18nKey"], "business.register")
        self.assertNotIn("sub", business_item)
        driver_item = next(item for item in response.data if item["app"] == "driver")
        self.assertEqual(driver_item["i18nKey"], "driver.register")
        self.assertNotIn("sub", driver_item)

    def test_unverified_user_sees_verification_prompt(self):
        self.user.is_identity_verified = False
        self.user.save(update_fields=["is_identity_verified"])
        url = reverse("kiini:user-menu")
        response = self.client.get(url)
        apps = [item["app"] for item in response.data]
        self.assertIn("verification", apps)

    def test_verified_user_does_not_see_verification_prompt(self):
        self.user.is_identity_verified = True
        self.user.is_phone_verified = True
        self.user.save(update_fields=["is_identity_verified", "is_phone_verified"])
        url = reverse("kiini:user-menu")
        response = self.client.get(url)
        apps = [item["app"] for item in response.data]
        self.assertNotIn("verification", apps)

    def test_business_owner_sees_business_dashboard_submenu(self):
        from businesses.models.business import Business
        Business.objects.create(owner=self.user, institution=self.institution, name="Test Biz")
        url = reverse("kiini:user-menu")
        response = self.client.get(url)
        business_item = next(item for item in response.data if item["app"] == "business")
        self.assertEqual(business_item["i18nKey"], "business.dashboard")
        self.assertTrue(len(business_item["sub"]) > 0)

    def test_driver_sees_driver_dashboard_submenu(self):
        from logistics.models.transport_provider import TransportProvider
        TransportProvider.objects.create(user=self.user)
        url = reverse("kiini:user-menu")
        response = self.client.get(url)
        driver_item = next(item for item in response.data if item["app"] == "driver")
        self.assertEqual(driver_item["i18nKey"], "driver.dashboard")
        self.assertTrue(len(driver_item["sub"]) > 0)


class DashboardContextTests(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Test Institution 2", domain="testdomain2")
        self.user = User.objects.create_user(
            email="context@test.com", password="pass1234", full_name="Context User",
        )
        self.user.institution = self.institution
        self.user.role = "CLIENT"
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_dashboard_context_defaults(self):
        url = reverse("kiini:dashboard-context")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_identity_verified"])
        self.assertIsNone(response.data["business"])
        self.assertIsNone(response.data["driver"])

    def test_dashboard_context_reflects_business_and_verification(self):
        from businesses.models.business import Business
        self.user.is_identity_verified = True
        self.user.is_phone_verified = True
        self.user.save(update_fields=["is_identity_verified", "is_phone_verified"])
        Business.objects.create(owner=self.user, institution=self.institution, name="Ctx Biz", is_verified=True)

        url = reverse("kiini:dashboard-context")
        response = self.client.get(url)
        self.assertTrue(response.data["is_identity_verified"])
        self.assertEqual(response.data["business"]["name"], "Ctx Biz")
        self.assertTrue(response.data["business"]["is_verified"])

    def test_dashboard_context_not_authenticated(self):
        self.client.logout()
        url = reverse("kiini:dashboard-context")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)