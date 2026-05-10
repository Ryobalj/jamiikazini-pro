# payments/webhooks/pawapay_webhook.py

import json
import hmac
import hashlib
import logging
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from payments.models import Invoice
from security.helpers.audit import AuditHelper
from security.helpers.alerts import send_slack_alert

logger = logging.getLogger(__name__)


def verify_signature(request) -> bool:
    """
    Verify Pawapay webhook signature using HMAC SHA256.
    """
    secret = settings.PAWAPAY.get("API_KEY")
    signature = request.headers.get("X-Pawapay-Signature")

    if not secret or not signature:
        return False

    computed = hmac.new(
        secret.encode("utf-8"),
        msg=request.body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


@method_decorator(csrf_exempt, name="dispatch")
class PawapayWebhookView(View):
    """
    Handle Pawapay webhook → link to Invoice.
    """

    def post(self, request, *args, **kwargs):
        # 🔐 Step 1: Verify signature
        if not verify_signature(request):
            logger.warning("[Pawapay Webhook] Invalid signature")
            return HttpResponseForbidden("Invalid signature")

        try:
            # 🔎 Step 2: Parse + sanitize payload
            payload = json.loads(request.body.decode("utf-8"))
            client_ref = str(payload.get("clientReference", "")).strip()
            status = str(payload.get("status", "")).upper().strip()
            amount = payload.get("amount")

            if not client_ref or not status:
                logger.error(f"[Pawapay Webhook] Missing fields in payload: {payload}")
                return JsonResponse({"error": "Invalid payload"}, status=400)

            # 🔗 Step 3: Locate Invoice
            invoice = Invoice.objects.filter(reference=client_ref).first()
            if not invoice:
                send_slack_alert(f"[Pawapay Webhook] Invoice not found for reference={client_ref}")
                return JsonResponse({"error": "Invoice not found"}, status=404)

            # 🔄 Step 4: Idempotency (avoid reprocessing)
            if invoice.status == "PAID" and status == "SUCCESS":
                return JsonResponse({"ok": True, "message": "Already processed"})

            # 🔐 Step 5: Validate amount consistency
            if amount and str(invoice.amount) != str(amount):
                send_slack_alert(
                    f"[Pawapay Webhook] Amount mismatch for invoice {invoice.id}: "
                    f"expected {invoice.amount}, got {amount}"
                )
                return JsonResponse({"error": "Amount mismatch"}, status=400)

            # 📝 Step 6: Update Invoice status
            if status == "SUCCESS":
                invoice.status = "PAID"
            elif status in ("FAILED", "CANCELLED"):
                invoice.status = "FAILED"
            elif status == "PENDING":
                invoice.status = "PENDING"

            invoice.save(update_fields=["status"])

            # 📜 Step 7: Audit log
            AuditHelper._audit(
                user=None,
                action="webhook_update",
                description=f"Pawapay webhook updated invoice {invoice.id}",
                request=request,
                meta=payload,
            )

            return JsonResponse({"ok": True})
        except Exception as e:
            logger.exception("[Pawapay Webhook] Processing error")
            send_slack_alert(f"[Pawapay Webhook] Failed to process webhook: {e}")
            return JsonResponse({"error": "internal error"}, status=500)
