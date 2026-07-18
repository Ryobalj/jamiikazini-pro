# logistics/services/weight_bands.py
#
# Business-rule bands mapping each vehicle_type to a reasonable weight, volume,
# and (for short-range or long-haul types) distance range - so a 1kg local
# parcel never gets offered Ship/Train/Air, and a multi-ton shipment never
# gets offered a boda_boda. Bands deliberately overlap (a 5kg item is valid on
# boda_boda, bajaji, AND tuk_tuk) - the goal is excluding nonsensical options,
# not picking one "correct" vehicle.
#
# Fields per band (all optional except min_kg):
#   min_kg, max_kg          - weight range the vehicle can carry
#   min_distance_km          - long-haul types (train/ship/air) aren't worth
#                              booking for short local trips
#   max_distance_km          - short-range types (daladala) shouldn't be
#                              offered for long-haul trips a bus/truck should do
#   max_volume_cbm           - excludes bulky-but-light loads from small
#                              vehicles that can't physically fit them

from logistics.choices import TransportTypeChoices

TRANSPORT_WEIGHT_BANDS = {
    TransportTypeChoices.BODA_BODA: {"min_kg": 0, "max_kg": 100, "max_volume_cbm": 0.3},
    TransportTypeChoices.BAJAJI: {"min_kg": 0, "max_kg": 300, "max_volume_cbm": 1.0},
    TransportTypeChoices.SUZUKI_CARRY: {"min_kg": 0, "max_kg": 600, "max_volume_cbm": 3.5},
    TransportTypeChoices.TUK_TUK: {"min_kg": 0, "max_kg": 1000, "max_volume_cbm": 2.0},
    TransportTypeChoices.PUBLIC_TRANSPORT: {"min_kg": 0, "max_kg": 1500, "max_distance_km": 20},
    TransportTypeChoices.BUS: {"min_kg": 0, "max_kg": 3000, "max_distance_km": 1000},
    TransportTypeChoices.CANTER: {"min_kg": 500, "max_kg": 3000},
    TransportTypeChoices.FUSO: {"min_kg": 2000, "max_kg": 8000},
    TransportTypeChoices.SCANIA: {"min_kg": 5000, "max_kg": 30000},
    TransportTypeChoices.TRAIN: {"min_kg": 2000, "max_kg": None, "min_distance_km": 150},
    TransportTypeChoices.SHIP: {"min_kg": 2000, "max_kg": None, "min_distance_km": 250},
    TransportTypeChoices.AIR: {"min_kg": 1, "max_kg": 1000, "min_distance_km": 250},
}


def is_vehicle_suitable(vehicle_type, weight_kg, distance_km, volume_cbm=None):
    band = TRANSPORT_WEIGHT_BANDS.get(vehicle_type)
    if band is None:
        return False
    if weight_kg < band.get("min_kg", 0):
        return False
    max_kg = band.get("max_kg")
    if max_kg is not None and weight_kg > max_kg:
        return False
    min_distance_km = band.get("min_distance_km")
    if min_distance_km is not None and distance_km < min_distance_km:
        return False
    max_distance_km = band.get("max_distance_km")
    if max_distance_km is not None and distance_km > max_distance_km:
        return False
    max_volume_cbm = band.get("max_volume_cbm")
    if max_volume_cbm is not None and volume_cbm is not None and volume_cbm > max_volume_cbm:
        return False
    return True


def suitable_vehicle_types(weight_kg, distance_km, volume_cbm=None):
    return {
        vehicle_type
        for vehicle_type in TRANSPORT_WEIGHT_BANDS
        if is_vehicle_suitable(vehicle_type, weight_kg, distance_km, volume_cbm)
    }
