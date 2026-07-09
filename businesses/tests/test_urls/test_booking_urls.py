import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework import status

# Bookings and their logs only exist as nested resources:
# /businesses/{b}/branches/{br}/services/{s}/bookings/{bk}/logs/
NIL = "00000000-0000-0000-0000-000000000000"
NEST = {"business_pk": NIL, "branch_pk": NIL, "service_pk": NIL}


@pytest.mark.django_db
class TestBookingURLs:

    def setup_method(self):
        self.client = APIClient()

    def test_booking_list_url_exists(self):
        url = reverse("businesses:service-bookings-list", kwargs=NEST)
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

    def test_booking_detail_url_404_for_nonexistent(self):
        url = reverse("businesses:service-bookings-detail", kwargs={**NEST, "pk": NIL})
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]

    def test_booking_log_list_url_exists(self):
        url = reverse("businesses:booking-logs-list", kwargs={**NEST, "booking_pk": NIL})
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

    def test_booking_log_detail_url_404_for_nonexistent(self):
        url = reverse("businesses:booking-logs-detail", kwargs={**NEST, "booking_pk": NIL, "pk": NIL})
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]
