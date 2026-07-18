# logistics/tests/test_delivery_quote_view.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from logistics.models.rate_card import TransportRateCard

pytestmark = pytest.mark.django_db


@pytest.fixture
def rate_cards(db):
    rates = {
        "boda_boda": (Decimal("1000"), Decimal("300"), Decimal("1500")),
        "bajaji": (Decimal("1300"), Decimal("350"), Decimal("1800")),
        "suzuki_carry": (Decimal("5000"), Decimal("700"), Decimal("7000")),
        "tuk_tuk": (Decimal("1500"), Decimal("400"), Decimal("2000")),
        "public_transport": (Decimal("1000"), Decimal("200"), Decimal("1500")),
        "bus": (Decimal("8000"), Decimal("900"), Decimal("10000")),
        "canter": (Decimal("10000"), Decimal("1500"), Decimal("15000")),
        "fuso": (Decimal("30000"), Decimal("3000"), Decimal("40000")),
        "scania": (Decimal("60000"), Decimal("5000"), Decimal("80000")),
        "train": (Decimal("50000"), Decimal("2000"), Decimal("60000")),
        "ship": (Decimal("80000"), Decimal("3000"), Decimal("100000")),
        "air": (Decimal("100000"), Decimal("5000"), Decimal("150000")),
    }
    for vehicle_type, (base, per_km, minimum) in rates.items():
        TransportRateCard.objects.create(
            vehicle_type=vehicle_type, base_fare=base, per_km_rate=per_km,
            minimum_fare=minimum, is_active=True,
        )


def _quote(client, weight_kg=None, pickup=(39.28, -6.80), dropoff=(39.20, -6.79)):
    params = {
        "pickup_lat": pickup[1], "pickup_lng": pickup[0],
        "dropoff_lat": dropoff[1], "dropoff_lng": dropoff[0],
    }
    if weight_kg is not None:
        params["weight_kg"] = weight_kg
    return client.get("/api/v1/logistics/delivery-quote/", params)


class TestDeliveryQuoteWeightFiltering:
    def test_small_local_weight_excludes_bulk_long_haul_types(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        response = _quote(client, weight_kg=1)
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}

        assert types & {"boda_boda", "tuk_tuk", "public_transport"}
        assert not types & {"canter", "fuso", "scania", "train", "ship", "air"}

    def test_heavy_long_distance_shipment_surfaces_bulk_freight(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        # ~0.9 degree separation * 100 ~= 90km isn't quite enough for train/ship's
        # 150/250km minimum distance bands, so pick points far enough apart.
        response = _quote(
            client, weight_kg=5000, pickup=(39.28, -6.80), dropoff=(36.80, -3.38)
        )
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}

        assert not types & {"boda_boda", "tuk_tuk", "public_transport"}
        assert "scania" in types

    def test_omitted_weight_defaults_to_5kg(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        response = _quote(client, weight_kg=None)
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}
        assert types & {"boda_boda", "tuk_tuk", "public_transport"}
        assert not types & {"train", "ship", "air"}

    def test_small_local_weight_surfaces_all_small_vehicle_types(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        response = _quote(client, weight_kg=5)
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}
        assert types & {"boda_boda", "bajaji", "suzuki_carry", "tuk_tuk", "public_transport"} == {
            "boda_boda", "bajaji", "suzuki_carry", "tuk_tuk", "public_transport"
        }

    def test_boda_boda_excluded_above_100kg_bajaji_still_offered(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        response = _quote(client, weight_kg=150)
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}
        assert "boda_boda" not in types
        assert "bajaji" in types

    def test_tuk_tuk_max_1000kg_suzuki_carry_max_600kg(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        response = _quote(client, weight_kg=800)
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}
        assert "suzuki_carry" not in types
        assert "tuk_tuk" in types

    def test_public_transport_excluded_beyond_20km_bus_offered_instead(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        # Pickup/dropoff ~55km apart - too far for daladala's 20km cap, well
        # within a bus's long-distance range.
        response = _quote(
            client, weight_kg=200, pickup=(39.28, -6.80), dropoff=(39.80, -6.80)
        )
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}
        assert "public_transport" not in types
        assert "bus" in types

    def test_public_transport_offered_within_20km(self, user_factory, rate_cards):
        client = APIClient()
        client.force_authenticate(user=user_factory(role="CLIENT"))

        response = _quote(client, weight_kg=200)
        assert response.status_code == status.HTTP_200_OK
        types = {q["vehicle_type"] for q in response.data["quotes"]}
        assert "public_transport" in types
