# payments/gateways/stripe/client.py

from __future__ import annotations
import json
import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError

from payments.gateways.base import BaseGateway, GatewayEvent

log = logging.getLogger("stripe")


class StripeGateway(BaseGateway):
    name = "stripe"

    def __init__(self):
        cfg = getattr(settings, "STRIPE", {})
        self.secret_key = cfg.get("SECRET_KEY")
        self.publishable_key = cfg.get("PUBLISHABLE_KEY")
        self.webhook_secret = cfg.get("WEBHOOK_SECRET")

        if not self.secret_key:
            raise ValidationError("STRIPE_SECRET_KEY missing in settings")

        self.base_url = "https://api.stripe.com/v1"
        self.timeout = 25
        self._session = requests.Session()

    # ---------- helpers
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        log.debug("POST %s %s", url, payload)
        resp = self._session.post(url, data=payload, headers=self._headers(), timeout=self.timeout)
        data = resp.json()
        if not resp.ok:
            log.error("Stripe error %s: %s", resp.status_code, data)
        resp.raise_for_status()
        return data

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        log.debug("GET %s", url)
        resp = self._session.get(url, headers=self._headers(), timeout=self.timeout)
        data = resp.json()
        if not resp.ok:
            log.error("Stripe error %s: %s", resp.status_code, data)
        resp.raise_for_status()
        return data

    # ---------- contract
    def initiate_deposit(
        self, *, amount: str, currency: str, email: str,
        client_reference_id: str, metadata: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Create a PaymentIntent for card deposits.
        """
        payload = {
            "amount": int(float(amount) * 100),  # stripe uses cents
            "currency": currency.lower(),
            "metadata[reference]": client_reference_id,
            "receipt_email": email,
        }
        if metadata:
            for k, v in metadata.items():
                payload[f"metadata[{k}]"] = v

        resp = self._post("/payment_intents", payload)
        return self.validate_payload(resp, required_keys=["id", "status", "client_secret"])

    def initiate_payout(
        self, *, amount: str, currency: str, account_id: str,
        client_reference_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Transfer (to connected account).
        """
        payload = {
            "amount": int(float(amount) * 100),
            "currency": currency.lower(),
            "destination": account_id,
            "transfer_group": client_reference_id,
        }
        if metadata:
            for k, v in metadata.items():
                payload[f"metadata[{k}]"] = v

        resp = self._post("/transfers", payload)
        return self.validate_payload(resp, required_keys=["id", "status"])

    def refund(self, *, stripe_charge_id: str, amount: Optional[str] = None) -> Dict[str, Any]:
        """
        Refund by charge ID.
        """
        payload: Dict[str, Any] = {"charge": stripe_charge_id}
        if amount:
            payload["amount"] = int(float(amount) * 100)

        resp = self._post("/refunds", payload)
        return self.validate_payload(resp, required_keys=["id", "status"])

    def check_transaction_status(self, stripe_payment_id: str) -> Dict[str, Any]:
        """
        Poll PaymentIntent status.
        """
        resp = self._get(f"/payment_intents/{stripe_payment_id}")
        return self.validate_payload(resp, required_keys=["id", "status"])

    # ---------- webhooks
    def verify_signature(self, *, headers: Dict[str, str], body: bytes) -> bool:
        """
        Verify Stripe webhook signature.
        """
        import stripe
        stripe.api_key = self.secret_key
        try:
            stripe.Webhook.construct_event(body, headers.get("Stripe-Signature"), self.webhook_secret)
            return True
        except Exception as e:
            log.warning("Invalid Stripe webhook signature: %s", e)
            return False

    def parse_webhook(self, *, headers: Dict[str, str], body: bytes) -> GatewayEvent:
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            raise ValidationError("Malformed webhook payload")

        event_type = payload.get("type")
        data = payload.get("data", {}).get("object", {})
        stripe_id = data.get("id")
        status = data.get("status")
        amount = str(data.get("amount") or "")
        currency = str(data.get("currency") or "").upper()

        return GatewayEvent(
            event_type=event_type,
            provider=self.name,
            provider_id=stripe_id,
            status=status.upper() if status else None,
            amount=str(int(amount) / 100) if amount else None,
            currency=currency or None,
            reference=data.get("metadata", {}).get("reference"),
            raw=payload,
        )