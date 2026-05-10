# logistics/constants/vehicle_types.py

from enum import Enum


class VehicleType(Enum):
    CAR = "CAR"
    MOTORCYCLE = "MOTORCYCLE"
    TRICIRCLE = "TRICIRCLE"
    BUS = "BUS"
    TRUCK = "TRUCK"
    SEMITRELLAR = "SEMITRELLAR"
    BOAT = "BOAT"
    DRONE = "DRONE"
    OTHER = "OTHER"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace('_', ' ').title()) for key in cls]