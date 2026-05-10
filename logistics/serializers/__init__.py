# logistics/serializers/__init__.py

from .transport_provider_serializer import (
    TransportProviderSerializer,
    TransportProviderVerificationSerializer,
    VerificationRequestStatusSerializer,
)

__all__ = [
    "TransportProviderSerializer",
    "TransportProviderVerificationSerializer",
    "VerificationRequestStatusSerializer",
]

from .driver_serializer import DriverSerializer