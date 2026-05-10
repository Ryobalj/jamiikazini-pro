# logistics/helpers/matching.py

from logistics.models import Vehicle
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance


def get_suitable_vehicles_for_request(request, max_distance_km=50):
    """
    Rudisha orodha ya magari yanayofaa kwa ombi fulani la usafiri.
    """

    weight = request.weight_kg
    volume = request.volume_cbm or 0
    suggested_type = request.suggested_transport_type
    pickup_point = request.pickup_location

    # Tafuta magari ya aina husika, yaliyo hai, yenye dereva, na yaliyothibitishwa
    vehicles = Vehicle.objects.filter(
        vehicle_type=suggested_type,
        is_active=True,
        active_driver__isnull=False
    ).annotate(
        distance=Distance("provider__location", pickup_point)
    ).filter(
        distance__lte=max_distance_km * 1000  # Convert km to meters
    ).order_by("distance")  # karibu kwanza

    suitable = []
    for v in vehicles:
        if v.is_fully_verified and (
            (v.capacity_kg is None or v.capacity_kg >= weight) and
            (v.volume_cbm is None or v.volume_cbm >= volume)
        ):
            suitable.append(v)

    return suitable
