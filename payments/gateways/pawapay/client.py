# payments/gateways/pawapay/client.py

from __future__ import annotations
import json
import logging
import uuid
from decimal import Decimal
import hmac
import hashlib
import base64
import time
from ipaddress import ip_address, ip_network
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError

from payments.gateways.base import BaseGateway, GatewayEvent

log = logging.getLogger("pawapay")


class PawaPayGateway(BaseGateway):
    name = "pawapay"

    def __init__(self):
        cfg = getattr(settings, "PAWAPAY", {})
        self.use_sandbox = cfg.get("USE_SANDBOX", True)
        self.base_url = cfg.get("SANDBOX_URL") if self.use_sandbox else cfg.get("LIVE_URL")

        # prefer explicit keys from .env if present
        self.api_key = (
            getattr(settings, "PAWAPAY_SANDBOX_API_KEY", None) if self.use_sandbox
            else getattr(settings, "PAWAPAY_LIVE_API_KEY", None)
        ) or cfg.get("API_KEY")  # fallback

        self.timeout = 20
        self._session = requests.Session()

    # -------- helpers
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
            log.error("PawaPay error %s: %s", resp.status_code, data)
        resp.raise_for_status()
        return data

    @staticmethod
    def _fmt_amount(amount) -> str:
        """
        PawaPay MNO za Afrika Mashariki (TZS/KES/UGX...) hazikubali desimali —
        '100.00' hukataliwa (INVALID_AMOUNT). Rudisha namba nzima kama string ('100').
        """
        return str(int(Decimal(str(amount))))

    # -------- contract
    def initiate_deposit(
        self, *, amount: str, currency: str, phone: str, provider: str,
        client_reference_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "depositId": str(uuid.uuid4()),
            "payer": {"type": "MMO", "accountDetails": {"phoneNumber": phone, "provider": provider}},
            "clientReferenceId": client_reference_id,
            "customerMessage": "Payment",
            "amount": self._fmt_amount(amount),
            "currency": currency,
            "metadata": [{str(k): str(v)} for k, v in (metadata or {}).items()],
        }
        resp = self._post("/v2/deposits", payload)
        self.validate_payload(resp, required_keys=["depositId", "status"])
        return resp  # rudisha jibu KAMILI (ikiwa na rejectionReason/failureReason n.k.)

    def initiate_payout(
        self, *, amount: str, currency: str, phone: str, provider: str,
        client_reference_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "payoutId": str(uuid.uuid4()),
            "recipient": {"type": "MMO", "accountDetails": {"phoneNumber": phone, "provider": provider}},
            "customerMessage": "Payout",
            "amount": self._fmt_amount(amount),
            "currency": currency,
            "metadata": [{str(k): str(v)} for k, v in (metadata or {}).items()],
        }
        resp = self._post("/v2/payouts", payload)
        self.validate_payload(resp, required_keys=["payoutId", "status"])
        return resp  # rudisha jibu KAMILI (ikiwa na rejectionReason n.k.)

    def refund(
        self, *, deposit_id: str, amount: str, currency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "refundId": str(uuid.uuid4()),
            "depositId": deposit_id,
            "amount": self._fmt_amount(amount),
            "currency": currency,
            "metadata": [{str(k): str(v)} for k, v in (metadata or {}).items()],
        }
        resp = self._post("/v2/refunds", payload)
        self.validate_payload(resp, required_keys=["refundId", "status"])
        return resp  # rudisha jibu KAMILI (ikiwa na rejectionReason n.k.)

    def check_transaction_status(self, client_reference_id: str) -> Dict[str, Any]:
        """
        Polls PawaPay API for the status of a deposit (top-up) using the client_reference_id.
        Returns a dict with at least {"status": "<status>"}
        """
        try:
            resp = self._post("/v2/deposits/status", {"clientReferenceId": client_reference_id})
            validated = self.validate_payload(resp, required_keys=["status", "depositId"])
            # normalize status to SUCCESS / FAILED / PENDING
            status = validated.get("status", "").upper()
            return {"status": status}
        except Exception as e:
            log.error(f"Failed to check PawaPay status for {client_reference_id}: {e}")
            return {"status": "FAILED"}

    # ---- webhooks
    def verify_signature(self, *, headers: Dict[str, str], body: bytes) -> bool:
        """
        Enforce webhook security:
        - HMAC SHA256 verification
        - Replay attack protection (5 min window)
        - Optional IP allowlist
        - Strict content-type check
        """
        if settings.DEBUG:
            return True

        # PawaPay v2 hutumia HTTP Message Signatures (RFC 9421) — scheme ya zamani ya
        # X-Pawapay-Signature HAITUMIKI, kwa hivyo ukaguzi wa chini hushindwa daima.
        # Usalama wa kuongeza salio unategemea UTHIBITISHO WA API (check_transaction_status)
        # kwenye webhook handler — ni wa kuaminika (unatumia API key yetu ya siri, hauamini
        # callback body). Weka PAWAPAY_VERIFY_WEBHOOK_SIGNATURE=true kuwezesha ukaguzi mkali
        # wa saini utakapotekelezwa kikamilifu (RFC 9421).
        if not getattr(settings, "PAWAPAY_VERIFY_WEBHOOK_SIGNATURE", False):
            return True

        secret = getattr(settings, "PAWAPAY_WEBHOOK_SECRET", None)
        if not secret:
            log.error("PAWAPAY_WEBHOOK_SECRET not configured")
            return False

        provided = headers.get("X-Pawapay-Signature")
        timestamp = headers.get("X-Pawapay-Timestamp")
        content_type = headers.get("Content-Type")

        if not (provided and timestamp):
            log.warning("Missing signature or timestamp")
            return False

        # 1. Strict content-type
        if content_type != "application/json":
            log.warning("Invalid content-type: %s", content_type)
            return False

        # 2. Replay protection (5 minutes)
        try:
            ts = int(timestamp)
        except ValueError:
            return False
        if abs(time.time() - ts) > 300:
            log.warning("Replay attack detected (timestamp too old)")
            return False

        # 3. HMAC SHA256 verification
        msg = f"{timestamp}.{body.decode()}".encode()
        expected = base64.b64encode(
            hmac.new(secret.encode(), msg, hashlib.sha256).digest()
        ).decode()
        if not hmac.compare_digest(provided, expected):
            log.warning("Invalid webhook signature")
            return False

        # 4. Optional IP allowlist
        allowed_ips = getattr(settings, "PAWAPAY_ALLOWED_IPS", [])
        if allowed_ips:
            remote_addr = headers.get("X-Forwarded-For") or headers.get("REMOTE_ADDR")
            if not remote_addr:
                return False
            try:
                if not any(ip_address(remote_addr) in ip_network(net) for net in allowed_ips):
                    log.warning("IP %s not in allowlist", remote_addr)
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
            log.error("Invalid webhook payload: %s", e)
            raise ValidationError("Malformed webhook payload")

        event_type = payload.get("type") or "unknown"
        data = payload.get("data") or payload

        provider_id = str(data.get("depositId") or data.get("payoutId") or data.get("refundId") or "").strip()
        status = str(data.get("status") or "").strip()
        amount = str(data.get("amount") or "").strip() or None
        currency = str(data.get("currency") or "").strip() or None
        ref = str(data.get("clientReferenceId") or data.get("reference") or "").strip() or None

        normalized = {
            "deposit.status": "DEPOSIT_STATUS",
            "payout.status": "PAYOUT_STATUS",
            "refund.status": "REFUND_STATUS",
        }.get(event_type, event_type.upper())

        return GatewayEvent(
            event_type=normalized,
            provider=self.name,
            provider_id=provider_id,
            status=status,
            amount=amount,
            currency=currency,
            reference=ref,
            raw=payload,
        )