# payments/views/webhook_api.py

from __future__ import annotations
import logging
import time

from django.conf import settings
from django.db import transaction as db_txn
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from payments.gateways.registry import get_gateway
from payments.gateways.base import GatewayEvent
from jamiiwallet.models.transaction import Transaction
from security.authentication.throttling import JamiiThrottle
from payments.models.audit_log import AuditLog
from security.helpers.alerts import send_slack_alert

log = logging.getLogger("payments.webhooks")


@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhookView(APIView):
    """
    Production-grade webhook handler:
    - Admin-triggered (JWT)
    - Provider webhook (HMAC/JWT signature)
    - Idempotency + replay protection
    - Audit trail + structured logs
    """

    authentication_classes = []  # handled manually
    permission_classes = [permissions.AllowAny]
    throttle_classes = [JamiiThrottle]

    def post(self, request, gateway: str, *args, **kwargs):
        body = request.body or b""
        headers = {k: v for k, v in request.headers.items()}
        client_ip = self.get_client_ip(request)

        # -----------------------
        # 0️⃣ IP Allowlist
        # -----------------------
        allowed_ips = getattr(settings, "PAYMENT_WEBHOOK_IPS", {}).get(gateway, [])
        if allowed_ips and client_ip not in allowed_ips:
            log.warning("Webhook rejected (IP not allowed): gateway=%s ip=%s", gateway, client_ip)
            return HttpResponse(status=403)

        # -----------------------
        # 1️⃣ Admin JWT verification
        # -----------------------
        auth_header = request.headers.get("Authorization")
        user = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split()[1]
            try:
                validated_token = JWTAuthentication().get_validated_token(token)
                validated_user = JWTAuthentication().get_user(validated_token)
                if not validated_user.is_staff:
                    raise AuthenticationFailed("Only staff can call this endpoint via JWT.")
                user = validated_user
            except Exception as e:
                log.warning("Invalid admin JWT: %s", str(e))
                return Response({"detail": "Invalid JWT"}, status=status.HTTP_401_UNAUTHORIZED)

        # -----------------------
        # 2️⃣ Provider signature verification
        # -----------------------
        gw = get_gateway(gateway)
        if not gw.verify_signature(headers=headers, body=body):
            log.warning("Invalid signature: gateway=%s ip=%s", gateway, client_ip)
            AuditLog.log("WEBHOOK_INVALID_SIGNATURE", user, f"Gateway={gateway}", ip=client_ip)
            return HttpResponse(status=401)

        # -----------------------
        # 3️⃣ Parse + replay protection
        # -----------------------
        try:
            event: GatewayEvent = gw.parse_webhook(headers=headers, body=body)
        except Exception as e:
            log.error("Failed to parse webhook: gateway=%s error=%s", gateway, e, exc_info=True)
            return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

        # Replay check (timestamp max_age=300s)
        if event.timestamp and (time.time() - event.timestamp > 300):
            log.warning("Stale webhook ignored: gateway=%s event_id=%s", gateway, event.id)
            return Response({"detail": "Stale webhook"}, status=status.HTTP_400_BAD_REQUEST)

        log.info("Webhook received: gateway=%s event_id=%s status=%s provider_id=%s reference=%s amount=%s",
                 gateway, event.id, event.status, event.provider_id, event.reference, event.amount)

        # -----------------------
        # 3.5️⃣ Wallet TopUp (deposit) crediting
        # -----------------------
        # PawaPay deposit callbacks hurejea TopUp yetu kwa clientReferenceId (reference)
        # AU depositId (provider_id). Tafuta kwa vyote viwili.
        topup = self._match_topup(event)
        if topup:
            return self._handle_topup_event(gw, topup, event, user, client_ip)

        # -----------------------
        # 4️⃣ Idempotency check
        # -----------------------
        if event.id and Transaction.objects.filter(last_event_id=event.id).exists():
            log.info("Duplicate webhook ignored: event_id=%s", event.id)
            return Response({"status": "duplicate"}, status=200)

        # -----------------------
        # 5️⃣ Reconcile Transaction
        # -----------------------
        if not event.provider_id:
            return Response({"detail": "Missing provider id"}, status=status.HTTP_400_BAD_REQUEST)

        with db_txn.atomic():
            try:
                txn = Transaction.objects.select_for_update().get(reference=event.provider_id)
            except Transaction.DoesNotExist:
                log.warning("Transaction not found: provider_id=%s gateway=%s", event.provider_id, gateway)
                return Response({"status": "ignored"}, status=200)

            old_status = txn.status
            if event.status in ("COMPLETED", "SUCCESS", "SUCCESSFUL"):
                if txn.status != Transaction.TransactionStatus.COMPLETED:
                    if txn.transaction_type == Transaction.TransactionType.TOP_UP:
                        from jamiiwallet.services.transaction_engine import TransactionEngine
                        TransactionEngine.process(txn)
                    txn.mark_completed()
            elif event.status in ("FAILED", "REJECTED", "DECLINED"):
                txn.mark_failed()

            # Attach webhook info
            receipt = txn.receipt or {}
            receipt["last_webhook"] = event.raw
            txn.receipt = receipt
            txn.last_event_id = event.id
            txn.save(update_fields=["status", "receipt", "updated_at", "last_event_id"])

            # Audit log
            AuditLog.log("WEBHOOK_PROCESSED", user, f"Gateway={gateway}, Event={event.id}",
                         ip=client_ip, txn_id=txn.id, old_status=old_status, new_status=txn.status)

        return Response({"ok": True})

    # -----------------------
    # TopUp helpers
    # -----------------------
    def _match_topup(self, event):
        """Tafuta TopUp kwa clientReferenceId (reference) AU depositId (provider_id)."""
        from jamiiwallet.models.topup import TopUp
        if event.reference:
            t = TopUp.objects.filter(reference=event.reference).select_related("user").first()
            if t:
                return t
        if event.provider_id:
            t = TopUp.objects.filter(metadata__depositId=event.provider_id).select_related("user").first()
            if t:
                return t
        return None

    def _handle_topup_event(self, gw, topup, event, user, client_ip):
        """
        Ongeza salio la wallet kwa TopUp iliyofaulu.
        USALAMA (tabaka): (1) idempotency — topup CONFIRMED/FAILED hairudiwi;
        (2) ukaguzi wa kiasi — event.amount lazima ilingane na topup.amount tuliyohifadhi;
        (3) tunaongeza KIASI TULICHOHIFADHI (topup.amount), si cha callback.
        Status hutoka kwenye callback ya PawaPay (inafika kwa HTTPS kutoka seva zao).
        (Uthibitisho wa saini RFC 9421 na API re-check ni uimarishaji wa baadaye —
        washa kwa PAWAPAY_VERIFY_WEBHOOK_SIGNATURE=true.)
        """
        from decimal import Decimal
        from jamiiwallet.models.topup import TopUp
        from jamiitasks.tasks.wallet import credit_wallet_for_topup

        # Idempotency: tayari imekamilika
        if topup.status in (TopUp.TopUpStatus.CONFIRMED, TopUp.TopUpStatus.FAILED):
            return Response({"status": "already_processed"}, status=200)

        api_status = (event.status or "").upper()

        if api_status in ("COMPLETED", "SUCCESS", "SUCCESSFUL"):
            # Amount safety: linganisha callback amount na kiasi tulichohifadhi
            if event.amount:
                try:
                    if Decimal(str(event.amount)) != Decimal(str(topup.amount)):
                        send_slack_alert(
                            f"[PawaPay] TopUp amount mismatch ref={topup.reference} "
                            f"expected={topup.amount} got={event.amount}"
                        )
                        return Response({"detail": "Amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)
                except Exception:
                    pass
            credit_wallet_for_topup(topup)
            try:
                AuditLog.log("WEBHOOK_TOPUP_CREDITED", user, f"ref={topup.reference}", ip=client_ip)
            except Exception:
                pass
            log.info("TopUp credited via webhook: ref=%s amount=%s", topup.reference, topup.amount)
            return Response({"ok": True})

        if api_status in ("FAILED", "REJECTED", "DECLINED", "CANCELLED"):
            topup.mark_failed()
            return Response({"ok": True, "status": "failed"})

        return Response({"status": "pending"}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

