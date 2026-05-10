# payments/gateways/base.py

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class GatewayEvent:
    """
    Normalized event from provider webhooks.

    Attributes:
        event_type: high-level type e.g. "DEPOSIT_COMPLETED", "PAYOUT_FAILED"
        provider: gateway name e.g. "pawapay"
        provider_id: unique provider reference (depositId/payoutId/refundId)
        status: raw status string from provider
        amount: optional Decimal amount (TZS) - None if unknown
        currency: optional currency code e.g. "TZS"
        reference: optional client reference / invoice number
        raw: original payload from provider
    """
    event_type: str
    provider: str
    provider_id: str
    status: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    reference: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class BaseGateway(ABC):
    """
    Contract / base class for all payment gateways.

    All gateways must implement:
    - deposit / payout / refund initiation
    - webhook verification & parsing

    Provides helper methods for common validation and type safety.
    """

    name: str  # lower_snake e.g. 'pawapay'

    # ---- Initiation (server → provider)
    @abstractmethod
    def initiate_deposit(
        self,
        *,
        amount: str,
        currency: str,
        phone: str,
        provider: str,
        client_reference_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def initiate_payout(
        self,
        *,
        amount: str,
        currency: str,
        phone: str,
        provider: str,
        client_reference_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def refund(
        self,
        *,
        deposit_id: str,
        amount: str,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        ...

    # ---- Webhook (provider → server)
    @abstractmethod
    def verify_signature(self, *, headers: Dict[str, str], body: bytes) -> bool:
        ...

    @abstractmethod
    def parse_webhook(self, *, headers: Dict[str, str], body: bytes) -> GatewayEvent:
        ...

    # ---- Helper methods
    @staticmethod
    def validate_payload(payload: Dict[str, Any], required_keys: list[str]) -> Dict[str, Any]:
        """
        Ensures provider payload has all required keys and strips whitespace.
        Raises ValueError if missing.
        """
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary.")
        sanitized = {}
        for key in required_keys:
            if key not in payload or payload[key] is None:
                raise ValueError(f"Missing required key: {key}")
            sanitized[key] = str(payload[key]).strip()
        return sanitized