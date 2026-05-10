import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework import status

@pytest.mark.django_db
class TestBookingURLs:

    def setup_method(self):
        self.client = APIClient()

    def test_booking_list_url_exists(self):
        url = reverse("businesses:booking-list")
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

    def test_booking_detail_url_404_for_nonexistent(self):
        url = reverse("businesses:booking-detail", args=["00000000-0000-0000-0000-000000000000"])
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]

    def test_booking_log_list_url_exists(self):
        url = reverse("businesses:booking-log-list")
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

    def test_booking_log_detail_url_404_for_nonexistent(self):
        url = reverse("businesses:booking-log-detail", args=["00000000-0000-0000-0000-000000000000"])
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]