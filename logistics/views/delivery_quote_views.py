# logistics/views/delivery_quote_views.py

from django.contrib.gis.geos import Point
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.choices import TransportTypeChoices
from logistics.models.rate_card import TransportRateCard
from logistics.services.weight_bands import suitable_vehicle_types


class DeliveryQuoteView(APIView):
    """Kadirio la bei ya usafiri kwa kila aina ya gari, kati ya sehemu mbili."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            pickup = Point(
                float(request.query_params["pickup_lng"]),
                float(request.query_params["pickup_lat"]),
                srid=4326,
            )
            dropoff = Point(
                float(request.query_params["dropoff_lng"]),
                float(request.query_params["dropoff_lat"]),
                srid=4326,
            )
        except (KeyError, TypeError, ValueError):
            raise ValidationError({"detail": "pickup_lat/pickup_lng/dropoff_lat/dropoff_lng zinahitajika."})

        try:
            weight_kg = float(request.query_params.get("weight_kg", 5.0))
        except (TypeError, ValueError):
            weight_kg = 5.0

        try:
            volume_cbm = float(request.query_params["volume_cbm"]) if request.query_params.get("volume_cbm") else None
        except (TypeError, ValueError):
            volume_cbm = None

        distance_km = pickup.distance(dropoff) * 100  # deg -> approx km, sawa na TransportRequest.calculate_distance_km()
        suitable_types = suitable_vehicle_types(weight_kg, distance_km, volume_cbm)

        rate_cards = {rc.vehicle_type: rc for rc in TransportRateCard.objects.filter(is_active=True)}
        quotes = []
        for vehicle_type, label in TransportTypeChoices.choices:
            if vehicle_type not in suitable_types:
                continue
            rate_card = rate_cards.get(vehicle_type)
            if not rate_card:
                continue
            quotes.append({
                "vehicle_type": vehicle_type,
                "label": label,
                "estimated_fare": rate_card.estimate_fare(distance_km),
            })

        return Response({"quotes": quotes, "distance_km": round(distance_km, 2)}, status=status.HTTP_200_OK)
