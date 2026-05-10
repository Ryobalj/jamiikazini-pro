# logistics/tests/test_transport_request.py

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from logistics.models.transport_request import TransportRequest
from logistics.factories import (
    TransportProviderFactory,
    VehicleFactory,
    BusinessFactory,
    UserFactory,
    InstitutionFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def institution():
    return InstitutionFactory()


@pytest.fixture
def client_user(institution):
    return UserFactory(institution=institution)


@pytest.fixture
def auth_client(client_user):
    client = APIClient()
    client.force_authenticate(user=client_user)
    return client


@pytest.fixture
def transport_provider(institution):
    return TransportProviderFactory(institution=institution)


@pytest.fixture
def vehicle(transport_provider):
    return VehicleFactory(provider=transport_provider)


@pytest.fixture
def business(institution):
    return BusinessFactory(institution=institution)


@pytest.fixture
def transport_request_data(business, vehicle):
    return {
        "business": business.id,
        "vehicle": vehicle.id,
        "pickup_location": {
            "type": "Point",
            "coordinates": [39.27, -6.80]
        },
        "dropoff_location": {
            "type": "Point",
            "coordinates": [39.28, -6.81]
        },
        "scheduled_time": "2025-06-01T10:00:00Z",
        "items_description": "Boxes of textbooks",
        "estimated_distance_km": 12.5,
        "estimated_cost": 35000,
    }


def test_create_transport_request(auth_client, transport_request_data):
    url = reverse("logistics:transportrequest-list")
    response = auth_client.post(url, data=transport_request_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert TransportRequest.objects.count() == 1
    assert TransportRequest.objects.first().items_description == "Boxes of textbooks"


def test_list_transport_requests(auth_client, transport_request_data):
    # Create two
    auth_client.post(reverse("logistics:transportrequest-list"), data=transport_request_data, format="json")
    auth_client.post(reverse("logistics:transportrequest-list"), data=transport_request_data, format="json")

    url = reverse("logistics:transportrequest-list")
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2


def test_get_transport_request_detail(auth_client, transport_request_data):
    res = auth_client.post(reverse("logistics:transportrequest-list"), data=transport_request_data, format="json")
    transport_id = res.data["id"]

    url = reverse("logistics:transportrequest-detail", args=[transport_id])
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["items_description"] == "Boxes of textbooks"


def test_update_transport_request(auth_client, transport_request_data):
    res = auth_client.post(reverse("logistics:transportrequest-list"), data=transport_request_data, format="json")
    transport_id = res.data["id"]

    update_url = reverse("logistics:transportrequest-detail", args=[transport_id])
    new_data = {"items_description": "Updated items"}
    response = auth_client.patch(update_url, new_data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["items_description"] == "Updated items"


def test_delete_transport_request(auth_client, transport_request_data):
    res = auth_client.post(reverse("logistics:transportrequest-list"), data=transport_request_data, format="json")
    transport_id = res.data["id"]

    delete_url = reverse("logistics:transportrequest-detail", args=[transport_id])
    response = auth_client.delete(delete_url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert TransportRequest.objects.count() == 0


def test_institution_data_is_isolated(auth_client, transport_request_data, institution):
    # Create from another institution
    other_institution = InstitutionFactory()
    other_user = UserFactory(institution=other_institution)
    other_client = APIClient()
    other_client.force_authenticate(user=other_user)

    # Create transport request for user's institution
    res = auth_client.post(reverse("logistics:transportrequest-list"), data=transport_request_data, format="json")
    transport_id = res.data["id"]

    # Another institution should not access it
    response = other_client.get(reverse("logistics:transportrequest-detail", args=[transport_id]))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_invalid_transport_request_fails(auth_client, transport_request_data):
    transport_request_data["estimated_distance_km"] = -5  # Invalid
    url = reverse("logistics:transportrequest-list")
    response = auth_client.post(url, data=transport_request_data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
