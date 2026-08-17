#logistics/models/__init__.py

from .transport_provider import TransportProvider
from .transport_provider_verification import TransportProviderVerification
from .driver import Driver
from .vehicle_verification import VehicleVerification
from .shipment import Shipment, ShipmentStatus
from .location import Location
from .transport_assignment import TransportAssignment
from .transport_leg import (
  TransportLeg,
  LegStatusLog,
  )
from .transport_request import TransportRequest
from .vehicle import Vehicle
from .rate_card import TransportRateCard
from .fare_proposal import FareProposal, FareProposalStatus
