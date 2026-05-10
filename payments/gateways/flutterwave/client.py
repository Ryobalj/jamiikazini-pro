# payments/gateways/flutterwave/client.py

from __future__ import annotations
import json
import logging
from ipaddress import ip_address, ip_network
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError

from payments.gateways.base import BaseGateway, GatewayEvent

log = logging.getLogger("flutterwave")


class FlutterwaveGateway(BaseGateway):
    name = "flutterwave"

    def __init__(self):
        cfg = getattr(settings, "FLUTTERWAVE", {})
        self.use_sandbox = cfg.get("USE_SANDBOX", True)
        self.base_url = cfg.get("SANDBOX_URL") if self.use_sandbox else cfg.get("LIVE_URL")

        # prefer explicit API key
        self.api_key = cfg.get("API_KEY")
        if not self.api_key:
            raise ValidationError("FLUTTERWAVE_API_KEY missing in settings")

        self.secret_hash = cfg.get("SECRET_HASH", "")
        self.timeout = 25
        self._session = requests.Session()

    # ---------- helpers
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        log.debug("POST %s %s", url, payload)
        resp = self._session.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            raise
        if not resp.ok:
            log.error("Flutterwave error %s: %s", resp.status_code, data)
        resp.raise_for_status()
        return data

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        log.debug("GET %s", url)
        resp = self._session.get(url, headers=self._headers(), timeout=self.timeout)
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            raise
        if not resp.ok:
            log.error("Flutterwave error %s: %s", resp.status_code, data)
        resp.raise_for_status()
        return data

    # ---------- contract
    def initiate_deposit(
        self, *, amount: str, currency: str, email: str, phone: Optional[str],
        client_reference_id: str, redirect_url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        For cards / mobile money deposits.
        """
        payload = {
            "tx_ref": client_reference_id,
            "amount": str(amount),
            "currency": currency,
            "redirect_url": redirect_url,
            "customer": {
                "email": email,
                "phonenumber": phone,
            },
            "meta": metadata or {},
        }
        resp = self._post("/payments", payload)
        return self.validate_payload(resp, required_keys=["status", "data"])

    def initiate_payout(
        self, *, amount: str, currency: str, account_number: str, bank_code: str,
        narration: str, client_reference_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Bank or mobile money transfer.
        """
        payload = {
            "account_bank": bank_code,
            "account_number": account_number,
            "amount": str(amount),
            "currency": currency,
            "narration": narration,
            "reference": client_reference_id,
            "meta": metadata or {},
        }
        resp = self._post("/transfers", payload)
        return self.validate_payload(resp, required_keys=["status", "data"])

    def refund(
        self, *, flw_ref: str, amount: Optional[str] = None, currency: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund by Flutterwave reference.
        """
        payload = {"amount": amount, "currency": currency} if amount else {}
        resp = self._post(f"/transactions/{flw_ref}/refund", payload)
        return self.validate_payload(resp, required_keys=["status"])

    def check_transaction_status(self, flw_txn_id: str) -> Dict[str, Any]:
        """
        Poll transaction status if webhook missed.
        """
        resp = self._get(f"/transactions/{flw_txn_id}/verify")
        return self.validate_payload(resp, required_keys=["status", "data"])

    # ---------- webhooks
    def verify_signature(self, *, headers: Dict[str, str], body: bytes) -> bool:
        """
        Enforce webhook security with secret hash + optional IP allowlist.
        """
        if settings.DEBUG:
            return True

        provided = headers.get("verif-hash")
        if not provided or provided != self.secret_hash:
            log.warning("Invalid or missing Flutterwave signature")
            return False

        # Optional IP check
        allowed_ips = getattr(settings, "FLUTTERWAVE", {}).get("ALLOWED_IPS", [])
        if allowed_ips:
            remote_addr = headers.get("X-Forwarded-For") or headers.get("REMOTE_ADDR")
            if not remote_addr:
                return False
            try:
                if not any(ip_address(remote_addr) in ip_network(net) for net in allowed_ips):
                    log.warning("Webhook IP %s not allowed", remote_addr)
                    return False
            except ValueError:
                log.warning("Invalid remote_addr: %s", remote_addr)
                return False

        return True

    def parse_webhook(self, *, headers: Dict[str, str], body: bytes) -> GatewayEvent:
        try:
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValidationError("Invalid webhook payload format")
        except Exception as e:
            log.error("Invalid Flutterwave webhook payload: %s", e)
            raise ValidationError("Malformed webhook payload")

        data = payload.get("data") or payload
        flw_ref = str(data.get("id") or data.get("tx_ref") or "").strip()
        status = str(data.get("status") or "").strip()
        amount = str(data.get("amount") or "").strip() or None
        currency = str(data.get("currency") or "").strip() or None

        return GatewayEvent(
            event_type="TRANSACTION_UPDATE",
            provider=self.name,
            provider_id=flw_ref,
            status=status.upper(),
            amount=amount,
            currency=currency,
            reference=data.get("tx_ref"),
            raw=payload,
        )