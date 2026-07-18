# logistics/tests/test_verification_gate.py
#
# Drivers must complete NIDA/license/LATRA verification (overall_status=VERIFIED)
# before they can accept a job (fast-accept) or submit a fare counter-offer.

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from kiini.models.institution import Institution
from logistics.models.transport_provider import TransportProvider
from logistics.models.transport_provider_verification import TransportProviderVerification
from logistics.models.vehicle import Vehicle
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_assignment import TransportAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def unverified_driver_with_vehicle(user_factory):
    institution, _ = Institution.objects.get_or_create(name="Test Logistics Co")
    driver_user = user_factory(role="TRANSPORTER")
    driver_user.institution = institution
    driver_user.save(update_fields=["institution"])
    provider = TransportProvider.objects.create(user=driver_user)
    vehicle = Vehicle.objects.create(provider=provider, vehicle_type="boda_boda", registration_number="T222UNV")
    return {"user": driver_user, "provider": provider, "vehicle": vehicle}


@pytest.fixture
def open_transport_request(business_factory):
    business = business_factory(location=Point(39.28, -6.80))
    return TransportRequest.objects.create(
        business=business,
        package_description="Parcel",
        weight_kg=5.0,
        pickup_location=Point(39.28, -6.80),
        dropoff_location=Point(39.20, -6.79),
        pickup_address_text="Dar es Salaam",
        dropoff_address_text="Kariakoo",
    )


def test_unverified_driver_cannot_fast_accept(unverified_driver_with_vehicle, open_transport_request):
    api = APIClient()
    api.force_authenticate(user=unverified_driver_with_vehicle["user"])
    url = reverse("logistics:assignment-assign-request", args=[open_transport_request.id])
    response = api.post(url, {"vehicle": unverified_driver_with_vehicle["vehicle"].id})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not TransportAssignment.objects.filter(transport_request=open_transport_request).exists()


def test_driver_with_pending_verification_cannot_fast_accept(unverified_driver_with_vehicle, open_transport_request):
    TransportProviderVerification.objects.create(
        user=unverified_driver_with_vehicle["user"],
        institution=unverified_driver_with_vehicle["user"].institution,
        overall_status="PENDING",
    )
    api = APIClient()
    api.force_authenticate(user=unverified_driver_with_vehicle["user"])
    url = reverse("logistics:assignment-assign-request", args=[open_transport_request.id])
    response = api.post(url, {"vehicle": unverified_driver_with_vehicle["vehicle"].id})

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_verified_driver_can_fast_accept(unverified_driver_with_vehicle, open_transport_request):
    TransportProviderVerification.objects.create(
        user=unverified_driver_with_vehicle["user"],
        institution=unverified_driver_with_vehicle["user"].institution,
        overall_status="VERIFIED",
    )
    api = APIClient()
    api.force_authenticate(user=unverified_driver_with_vehicle["user"])
    url = reverse("logistics:assignment-assign-request", args=[open_transport_request.id])
    response = api.post(url, {"vehicle": unverified_driver_with_vehicle["vehicle"].id})

    assert response.status_code == status.HTTP_201_CREATED, response.data


def test_unverified_driver_cannot_submit_fare_proposal(unverified_driver_with_vehicle, open_transport_request):
    api = APIClient()
    api.force_authenticate(user=unverified_driver_with_vehicle["user"])
    response = api.post(
        "/api/v1/logistics/fare-proposals/",
        {
            "transport_request": str(open_transport_request.id),
            "vehicle": unverified_driver_with_vehicle["vehicle"].id,
            "proposed_fare": "5000.00",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
