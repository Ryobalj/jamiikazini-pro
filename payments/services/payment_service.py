# payments/services/payment_service.py

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any, List, Tuple

from django.db import transaction as db_txn
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

import logging
import re
import traceback
import uuid

from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine
from jamiitasks.tasks.payments_gateway_tasks import poll_transaction_status

from payments.gateways.registry import get_gateway
from payments.models.invoice import Invoice
from payments.models.audit_log import AuditLog
from payments.models.paymentmethod import PaymentMethod, PaymentMethodType
from security.helpers.payment_otp import enforce_high_value_otp
from security.helpers.security import BaseLoginLogger
from security.helpers.alerts import send_slack_alert
from payments.services.currency_service import get_default_currency_code

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Unified PaymentService for deposits, payouts, refunds and generic payments.
    - Keeps current behaviour for deposit/payout/refund intact.
    - Adds process_payment to support WALLET, PAWAPAY, CARD and BANK flows.
    - Adds more robust provider response extraction & validation and safer polling scheduling.
    """

    # ------------------- helpers -------------------
    @staticmethod
    def _audit(user, action: str, description: str, request=None, **meta):
        try:
            ip_address = "0.0.0.0"
            if request:
                ip_address = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR", "0.0.0.0")
                # Get first IP if multiple in X-Forwarded-For
                ip_address = ip_address.split(",")[0].strip()
                try:
                    import ipaddress
                    ipaddress.ip_address(ip_address)  # validate format
                except Exception:
                    ip_address = "0.0.0.0"

            metadata = dict(meta) if isinstance(meta, dict) else {}

            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                action=action,
                description=description,
                metadata=metadata,
                ip_address=ip_address,
            )
        except Exception as e:
            user_id = getattr(user, "id", None)
            logger.exception("Failed to write audit log")
            try:
                send_slack_alert(f"[Audit Log Failure] user={user_id} action={action} error={e}")
            except Exception:
                logger.debug("send_slack_alert failed for audit failure", exc_info=True)

    @staticmethod
    def _get_gateway_from_method(pm: PaymentMethod) -> str:
        if pm.method_type == PaymentMethodType.PAWAPAY:
            return "pawapay"
        elif pm.method_type == PaymentMethodType.WALLET:
            return "wallet"
        elif pm.method_type == PaymentMethodType.CREDIT_CARD:
            # map credit card to a named gateway (stripe/flutterwave) via metadata if present
            # If payment method carries gateway hint, use it; otherwise return generic 'credit_card'
            hint = (pm.metadata or {}).get("gateway") if hasattr(pm, "metadata") else None
            return (hint or "credit_card").lower()
        else:
            return (pm.method_type or "").lower()

    @staticmethod
    def _sanitize_input(value: Any) -> str:
        """Sanitize input to prevent XSS and injection attacks"""
        if value is None:
            return ""

        sanitized = str(value).strip()
        # Remove potentially dangerous characters
        sanitized = sanitized.replace("<", "&lt;").replace(">", "&gt;")
        sanitized = sanitized.replace("'", "&#x27;").replace('"', "&quot;")
        sanitized = sanitized.replace("(", "&#40;").replace(")", "&#41;")
        # avoid removing benign substrings too aggressively — only remove obvious script/eval tokens
        sanitized = re.sub(r"(?i)\beval\b", "", sanitized)
        sanitized = re.sub(r"(?i)\bscript\b", "", sanitized)

        return sanitized

    @staticmethod
    def _validate_pawapay_response(resp: dict):
        """Validate PawaPay specific response format"""
        # Accept nested 'data' responses where provider returns {"data": {...}}
        candidate = resp.get("data") if isinstance(resp.get("data"), dict) else resp

        if "depositId" in candidate and not re.match(r"^dp_[a-zA-Z0-9]{8,64}$", str(candidate["depositId"])):
            raise ValidationError("Invalid PawaPay deposit ID format")

        if "payoutId" in candidate and not re.match(r"^po_[a-zA-Z0-9]{8,64}$", str(candidate["payoutId"])):
            raise ValidationError("Invalid PawaPay payout ID format")

        if "refundId" in candidate and not re.match(r"^rf_[a-zA-Z0-9]{8,64}$", str(candidate["refundId"])):
            raise ValidationError("Invalid PawaPay refund ID format")

        if "amount" in candidate:
            try:
                amount = Decimal(str(candidate["amount"]))
                if amount <= 0:
                    raise ValidationError("Amount must be positive in PawaPay response")
            except (InvalidOperation, TypeError):
                raise ValidationError("Invalid amount in PawaPay response")

        valid_statuses = ["PENDING", "COMPLETED", "FAILED", "SUCCESS", "SUCCESSFUL", "REJECTED", "DECLINED"]
        if "status" in candidate and str(candidate["status"]).upper() not in valid_statuses:
            raise ValidationError(f"Invalid status in PawaPay response: {candidate.get('status')}")

    @staticmethod
    def _validate_credit_card_response(resp: dict):
        """Validate Credit Card specific response format (generic)"""
        candidate = resp.get("data") if isinstance(resp.get("data"), dict) else resp

        if "transactionId" in candidate and not re.match(r"^[a-zA-Z0-9_-]{8,64}$", str(candidate["transactionId"])):
            raise ValidationError("Invalid credit card transaction ID format")

        if "authCode" in candidate and not re.match(r"^[A-Z0-9]{4,16}$", str(candidate["authCode"])):
            raise ValidationError("Invalid credit card authorization code format")

        if "amount" in candidate:
            try:
                amount = Decimal(str(candidate["amount"]))
                if amount <= 0:
                    raise ValidationError("Amount must be positive in credit card response")
            except (InvalidOperation, TypeError):
                raise ValidationError("Invalid amount in credit card response")

    @staticmethod
    def _validate_provider_response(resp: dict, required_keys: List[str], gateway_name: str) -> Dict[str, str]:
        """
        Ensure provider response contains required keys and sanitize values.
        Accepts responses where keys may be under a 'data' envelope.
        Returns sanitized mapping for the requested keys (strings).
        """
        if not isinstance(resp, dict):
            raise ValidationError("Provider response must be a dictionary.")

        # allow provider to wrap useful payload under "data"
        candidate = resp.get("data") if isinstance(resp.get("data"), dict) else resp

        missing = []
        for key in required_keys:
            if key not in candidate or candidate[key] is None:
                missing.append(key)
        if missing:
            # try alternative common keys (e.g. 'id', 'tx_ref', 'reference') for leniency
            alt_map = {
                "depositId": ["id", "tx_ref", "reference", "deposit_id", "transaction_id"],
                "payoutId": ["id", "reference", "payout_id", "transaction_id"],
                "refundId": ["id", "reference", "refund_id"],
                "status": ["status", "transaction_status", "result", "state"],
            }
            for key in missing[:]:
                alts = alt_map.get(key, [])
                for a in alts:
                    if a in candidate and candidate[a] is not None:
                        candidate[key] = candidate[a]
                        missing.remove(key)
                        break

        if missing:
            raise ValidationError(f"Provider response missing required key(s): {', '.join(missing)}")

        # Gateway-specific validation
        if gateway_name == "pawapay":
            PaymentService._validate_pawapay_response(resp)
        elif gateway_name in ("stripe", "flutterwave", "credit_card"):
            PaymentService._validate_credit_card_response(resp)

        # Sanitize values for required keys
        sanitized: Dict[str, str] = {}
        for key in required_keys:
            val = candidate.get(key)
            sanitized[key] = PaymentService._sanitize_input(val)
        return sanitized

    @staticmethod
    def _extract_provider_id(resp: dict, gateway_name: str, prefer: List[str]) -> Optional[str]:
        """
        Robustly extract provider-specific ID from a response. `prefer` is a list of candidate keys in priority order.
        """
        if not isinstance(resp, dict):
            return None
        candidate = resp.get("data") if isinstance(resp.get("data"), dict) else resp
        for k in prefer:
            v = candidate.get(k)
            if v:
                return str(v).strip()
        # try flatter alternatives
        for k, v in candidate.items():
            if k.lower().endswith("id") and v:
                return str(v).strip()
        return None

    @staticmethod
    def _validate_amount(amount):
        try:
            dec = Decimal(amount)
            if dec <= 0:
                raise ValidationError("Amount must be positive")
            # quantize to 2 decimal places
            return dec.quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError):
            raise ValidationError(f"Invalid amount: {amount}")

    @staticmethod
    def _validate_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Validate webhook signature to ensure authenticity.
        Implement based on your gateway's signature method.
        """
        # This is a placeholder - implement based on your gateway's requirements
        # Example: HMAC validation
        try:
            import hmac
            import hashlib

            computed_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(computed_signature, signature)
        except Exception:
            return False

    # ------------------- deposit -------------------
    @staticmethod
    def deposit(*, user, amount: Decimal, payment_method: PaymentMethod,
                invoice: Optional[Invoice] = None, metadata: Optional[Dict[str, Any]] = None,
                request=None) -> Dict[str, Any]:

        currency = payment_method.currency or get_default_currency_code()
        if request:
            enforce_high_value_otp(request, user, amount, currency=currency)

        gateway_name = PaymentService._get_gateway_from_method(payment_method)
        gw = None
        try:
            gw = get_gateway(gateway_name)
        except Exception as e:
            logger.exception("Failed to resolve gateway for deposit")
            send_slack_alert(f"Gateway lookup failed: {gateway_name} error={e}")
            raise ValidationError(f"Gateway '{gateway_name}' not available")

        amount_dec = PaymentService._validate_amount(amount)
        client_ref = invoice.invoice_number if invoice else f"USR-{user.id}"

        # call provider
        try:
            resp = gw.initiate_deposit(
                amount=str(amount_dec),
                currency=currency,
                phone=payment_method.account_identifier,
                provider=getattr(payment_method, "mno", None),
                client_reference_id=client_ref,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.exception("Provider initiate_deposit failed")
            send_slack_alert(f"Deposit initiation failed user={getattr(user,'id',None)} gw={gateway_name} error={e}")
            raise

        # attempt to extract deposit id from various fields
        deposit_id = PaymentService._extract_provider_id(resp, gateway_name, prefer=["depositId", "id", "tx_ref", "reference", "transactionId"])
        try:
            sanitized = PaymentService._validate_provider_response(resp, required_keys=["depositId", "status"], gateway_name=gateway_name)
            deposit_id = sanitized.get("depositId") or deposit_id
            status = sanitized.get("status")
        except ValidationError:
            # fallback: if provider returned different keys but still ok, try to continue using extracted id
            status = (resp.get("status") or (resp.get("data") or {}).get("status") or "").upper()

        if not deposit_id:
            logger.error("Could not extract deposit id from provider response: %s", resp)
            raise ValidationError("Provider response missing deposit identifier")

        with db_txn.atomic():
            # keep original behavior: obtain wallet & create txn via TransactionEngine
            wallet = Wallet.objects.select_for_update().get(user=user)
            txn = TransactionEngine.initiate(
                wallet=wallet,
                initiated_by=user,
                transaction_type=Transaction.TransactionType.TOP_UP,
                amount=amount_dec,
                idempotency_key=deposit_id,
                receipt={"provider": gateway_name, "init": resp},
            )

        # trigger polling task (best-effort scheduling)
        try:
            # tasks expect args: gateway_name, provider_id, txn_ref (see poll_task usage)
            poll_transaction_status.apply_async(
                args=(gateway_name, deposit_id, txn.reference),
                countdown=60  # start after 1 min
            )
        except Exception:
            logger.exception("Failed to schedule poll_transaction_status task (non-fatal)")

        PaymentService._audit(user, "DEPOSIT_INIT", "Deposit initiated via provider", request,
                              provider=gateway_name, deposit_id=deposit_id, amount=str(amount_dec))
        if request:
            try:
                BaseLoginLogger.log_success(request, user)
            except Exception as e:
                logger.debug("BaseLoginLogger.log_success failed", exc_info=True)
                try:
                    send_slack_alert(f"Login logger failed for user {user.id}: {e}")
                except Exception:
                    logger.debug("send_slack_alert also failed")

        return {"provider": gateway_name, "depositId": deposit_id, "status": status, "tx": txn.reference}

    # ------------------- payout -------------------
    @staticmethod
    def payout(*, user, amount: Decimal, payment_method: PaymentMethod,
               metadata: Optional[Dict[str, Any]] = None, request=None) -> Dict[str, Any]:

        currency = payment_method.currency or get_default_currency_code()
        if request:
            enforce_high_value_otp(request, user, amount, currency=currency)

        gateway_name = PaymentService._get_gateway_from_method(payment_method)
        gw = None
        try:
            gw = get_gateway(gateway_name)
        except Exception as e:
            logger.exception("Failed to resolve gateway for payout")
            send_slack_alert(f"Payout gateway lookup failed: {gateway_name} error={e}")
            raise ValidationError(f"Gateway '{gateway_name}' not available")

        amount_dec = PaymentService._validate_amount(amount)
        client_ref = f"PAYOUT-{user.id}-{int(timezone.now().timestamp())}"

        try:
            resp = gw.initiate_payout(
                amount=str(amount_dec),
                currency=currency,
                phone=payment_method.account_identifier,
                provider=getattr(payment_method, "mno", None),
                client_reference_id=client_ref,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.exception("Provider initiate_payout failed")
            send_slack_alert(f"Payout initiation failed user={getattr(user,'id',None)} gw={gateway_name} error={e}")
            raise

        payout_id = PaymentService._extract_provider_id(resp, gateway_name, prefer=["payoutId", "id", "reference"])
        try:
            sanitized = PaymentService._validate_provider_response(resp, required_keys=["payoutId", "status"], gateway_name=gateway_name)
            payout_id = sanitized.get("payoutId") or payout_id
            status = sanitized.get("status")
        except ValidationError:
            status = (resp.get("status") or (resp.get("data") or {}).get("status") or "").upper()

        if not payout_id:
            logger.error("Could not extract payout id from provider response: %s", resp)
            raise ValidationError("Provider response missing payout identifier")

        with db_txn.atomic():
            wallet = Wallet.objects.select_for_update().get(user=user)
            txn = TransactionEngine.initiate(
                wallet=wallet,
                initiated_by=user,
                transaction_type=Transaction.TransactionType.WITHDRAWAL,
                amount=amount_dec,
                idempotency_key=payout_id,
                receipt={"provider": gateway_name, "init": resp},
            )

        try:
            poll_transaction_status.apply_async(
                args=(gateway_name, payout_id, txn.reference),
                countdown=60
            )
        except Exception:
            logger.exception("Failed to schedule payout poll task (non-fatal)")

        PaymentService._audit(user, "PAYOUT_INIT", "Payout initiated via provider", request,
                              provider=gateway_name, payout_id=payout_id, amount=str(amount_dec))
        if request:
            try:
                BaseLoginLogger.log_success(request, user)
            except Exception as e:
                logger.debug("BaseLoginLogger.log_success failed", exc_info=True)
                try:
                    send_slack_alert(f"Login logger failed for user {user.id}: {e}")
                except Exception:
                    logger.debug("send_slack_alert also failed")

        return {"provider": gateway_name, "payoutId": payout_id, "status": status, "tx": txn.reference}

    # ------------------- refund -------------------
    @staticmethod
    def refund(*, user, txn: Transaction, amount: Decimal, payment_method: PaymentMethod,
               metadata: Optional[Dict[str, Any]] = None, request=None) -> Dict[str, Any]:

        currency = payment_method.currency or get_default_currency_code()
        if request:
            enforce_high_value_otp(request, user, amount, currency=currency)

        gateway_name = PaymentService._get_gateway_from_method(payment_method)
        gw = None
        try:
            gw = get_gateway(gateway_name)
        except Exception as e:
            logger.exception("Failed to resolve gateway for refund")
            send_slack_alert(f"Refund gateway lookup failed: {gateway_name} error={e}")
            raise ValidationError(f"Gateway '{gateway_name}' not available")

        amount_dec = PaymentService._validate_amount(amount)
        client_ref = f"REFUND-{txn.reference}"

        try:
            # Many gateways accept different param names — call with commonly used names
            resp = gw.refund(
                deposit_id=getattr(txn, "reference", None) or getattr(txn, "id", None),
                amount=str(amount_dec),
                currency=currency,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.exception("Provider refund call failed")
            send_slack_alert(f"Refund initiation failed user={getattr(user,'id',None)} gw={gateway_name} error={e}")
            raise

        refund_id = PaymentService._extract_provider_id(resp, gateway_name, prefer=["refundId", "id", "reference"])
        try:
            sanitized = PaymentService._validate_provider_response(resp, required_keys=["refundId", "status"], gateway_name=gateway_name)
            refund_id = sanitized.get("refundId") or refund_id
            status = sanitized.get("status")
        except ValidationError:
            status = (resp.get("status") or (resp.get("data") or {}).get("status") or "").upper()

        if not refund_id:
            logger.error("Could not extract refund id from provider response: %s", resp)
            raise ValidationError("Provider response missing refund identifier")

        with db_txn.atomic():
            txn_refund = TransactionEngine.initiate(
                wallet=txn.wallet,
                initiated_by=user,
                transaction_type=Transaction.TransactionType.REFUND,
                amount=amount_dec,
                idempotency_key=refund_id,
                receipt={"provider": gateway_name, "init": resp},
            )

        PaymentService._audit(user, "REFUND_INIT", f"Refund initiated for txn {txn.reference}", request,
                              provider=gateway_name, refund_id=refund_id, amount=str(amount_dec))
        if request:
            try:
                BaseLoginLogger.log_success(request, user)
            except Exception as e:
                logger.debug("BaseLoginLogger.log_success failed", exc_info=True)
                try:
                    send_slack_alert(f"Login logger failed for user {user.id}: {e}")
                except Exception:
                    logger.debug("send_slack_alert also failed")
        return {"provider": gateway_name, "refundId": refund_id, "status": status, "tx": txn_refund.reference}

    # ------------------- process_payment -------------------
    @staticmethod
    def process_payment(
        *,
        user,
        amount: Decimal,
        payment_method: PaymentMethod,
        invoice: Optional[Invoice] = None,
        recipient_user=None,
        recipient_wallet: Optional[Wallet] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request=None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:

        currency = payment_method.currency or get_default_currency_code()
        try:
            if request:
                enforce_high_value_otp(request, user, amount, currency=currency)
            amount_dec = PaymentService._validate_amount(amount)

            method_type = payment_method.method_type
            gateway_name = PaymentService._get_gateway_from_method(payment_method)
            gw = None
            if method_type != PaymentMethodType.WALLET:
                try:
                    gw = get_gateway(gateway_name)
                except Exception as e:
                    send_slack_alert(f"Gateway fetch failed for user {user.id} method {method_type}: {e}")
                    gw = None

            # Wallet → transfer
            if method_type == PaymentMethodType.WALLET:
                if not recipient_wallet:
                    if invoice:
                        recipient_user = invoice.user
                    if recipient_user:
                        recipient_wallet = Wallet.objects.select_for_update().get(user=recipient_user)
                if not recipient_wallet:
                    raise ValidationError("Recipient wallet is required for WALLET payments (provide invoice or recipient_user).")

                payer_wallet = Wallet.objects.select_for_update().get(user=user)
                recipient_user = recipient_wallet.user
                # Engine signature: initiate(account_identifier, amount, txn_type, metadata).
                # Preprocessor inahitaji source_txn_id + merchant_id; TRANSFER inahitaji recipient_id.
                # counterparty (User FK) na wallet huwekwa baada ya initiate.
                txn_metadata = {
                    "source_txn_id": idempotency_key or uuid.uuid4().hex,
                    "merchant_id": "JAMIIKAZINI",
                    "recipient_id": str(recipient_user.id),
                    **(metadata or {}),
                }
                txn = TransactionEngine.initiate(
                    account_identifier=user.email,
                    amount=amount_dec,
                    txn_type=Transaction.TransactionType.TRANSFER,
                    metadata=txn_metadata,
                )
                txn.counterparty = recipient_user
                txn.wallet = payer_wallet
                txn.save(update_fields=["counterparty", "wallet"])
                txn = TransactionEngine.process(txn)

                if invoice and txn.status == Transaction.TransactionStatus.COMPLETED:
                    try:
                        invoice.mark_as_paid(paid_at=timezone.now())
                    except Exception as e:
                        logger.exception("Failed to mark invoice as paid for invoice=%s", getattr(invoice, "id", None))
                        try:
                            send_slack_alert(f"Invoice mark_as_paid failed invoice={getattr(invoice,'id',None)} error={e}")
                        except Exception:
                            logger.debug("send_slack_alert failed for invoice failure", exc_info=True)

                PaymentService._audit(user, "PAYMENT_EXECUTED", "Wallet payment executed", request,
                                      amount=str(amount_dec), tx=txn.reference,
                                      recipient=getattr(recipient_wallet, "user_id", None))
                if request:
                    try:
                        BaseLoginLogger.log_success(request, user)
                    except Exception as e:
                        logger.debug("BaseLoginLogger.log_success failed", exc_info=True)
                        try:
                            send_slack_alert(f"Login logger failed for user {user.id}: {e}")
                        except Exception:
                            logger.debug("send_slack_alert also failed")
                return {"status": txn.status, "tx": txn.reference}

            # External gateway payments
            if not gw:
                raise ValidationError(f"No gateway configured for method {method_type}")

            client_ref = invoice.invoice_number if invoice else f"USR-{user.id}-{int(timezone.now().timestamp())}"

            try:
                resp = gw.initiate_deposit(
                    amount=str(amount_dec),
                    currency=currency,
                    phone=payment_method.account_identifier,
                    provider=getattr(payment_method, "mno", None),
                    client_reference_id=client_ref,
                    metadata=metadata or {},
                )
            except Exception as e:
                logger.exception("Gateway initiate_deposit failed")
                send_slack_alert(f"External payment initiation failed user={getattr(user,'id',None)} gw={gateway_name} error={e}")
                raise

            deposit_id = PaymentService._extract_provider_id(resp, gateway_name, prefer=["depositId", "id", "tx_ref", "reference", "transactionId"])
            try:
                sanitized = PaymentService._validate_provider_response(resp, required_keys=["depositId", "status"], gateway_name=gateway_name)
                deposit_id = sanitized.get("depositId") or deposit_id
                status = sanitized.get("status")
            except ValidationError:
                status = (resp.get("status") or (resp.get("data") or {}).get("status") or "").upper()

            if not deposit_id:
                logger.error("Could not extract deposit id from provider response for payment: %s", resp)
                raise ValidationError("Provider response missing deposit identifier")

            with db_txn.atomic():
                wallet = Wallet.objects.select_for_update().get(user=user)
                txn = TransactionEngine.initiate(
                    wallet=wallet,
                    initiated_by=user,
                    transaction_type=Transaction.TransactionType.TOP_UP,
                    amount=amount_dec,
                    idempotency_key=deposit_id,
                    receipt={"provider": gateway_name, "init": resp},
                )

            PaymentService._audit(user, "PAYMENT_INIT", "External payment initiated", request,
                                  provider=gateway_name, deposit_id=deposit_id, amount=str(amount_dec))
            if request:
                try:
                    BaseLoginLogger.log_success(request, user)
                except Exception as e:
                    logger.debug("BaseLoginLogger.log_success failed", exc_info=True)
                    try:
                        send_slack_alert(f"Login logger failed for user {user.id}: {e}")
                    except Exception:
                        logger.debug("send_slack_alert also failed")

            # schedule poll to reconcile if webhook missed
            try:
                poll_transaction_status.apply_async(
                    args=(gateway_name, deposit_id, txn.reference),
                    countdown=60
                )
            except Exception:
                logger.exception("Failed to schedule payment poll task (non-fatal)")

            return {"provider": gateway_name, "depositId": deposit_id, "status": status, "tx": txn.reference}

        except Exception as e:
            logger.exception("Payment processing failed: %s", traceback.format_exc())
            try:
                send_slack_alert(f"[Payment Failed] user={getattr(user,'id',None)} amount={amount} currency={currency} error={e}")
            except Exception:
                logger.debug("send_slack_alert failed for payment failure", exc_info=True)
            raise

    # ------------------- reconcile_event -------------------
    @staticmethod
    def reconcile_event(txn: Transaction, event, signature: str = None):
        """
        Reconcile webhook events with validation
        """
        # Validate webhook signature if available
        if signature:
            # determine secret from provider stored in txn.receipt if possible
            provider = (txn.receipt or {}).get("provider") or "pawapay"
            secret = ""
            try:
                secret = getattr(settings, provider.upper(), {}).get("WEBHOOK_SECRET", "") if provider else ""
            except Exception:
                secret = ""
            if secret and not PaymentService._validate_webhook_signature(event.raw, signature, secret):
                logger.warning(f"Invalid webhook signature for txn {txn.reference}")
                raise ValidationError("Invalid webhook signature")

        # Sanitize webhook data before storing
        raw_data = event.raw
        if isinstance(raw_data, dict):
            sanitized_data = {k: PaymentService._sanitize_input(v) for k, v in raw_data.items()}
        else:
            sanitized_data = PaymentService._sanitize_input(str(raw_data))

        with db_txn.atomic():
            txn = Transaction.objects.select_for_update().get(pk=txn.pk)

            status_map = {
                "COMPLETED": Transaction.TransactionStatus.COMPLETED,
                "SUCCESS": Transaction.TransactionStatus.COMPLETED,
                "SUCCESSFUL": Transaction.TransactionStatus.COMPLETED,
                "FAILED": Transaction.TransactionStatus.FAILED,
                "REJECTED": Transaction.TransactionStatus.FAILED,
                "DECLINED": Transaction.TransactionStatus.FAILED,
            }

            new_status = status_map.get((event.status or "").upper() if hasattr(event, 'status') else None)
            if not new_status:
                logger.warning(f"Unknown status in webhook: {getattr(event, 'status', 'None')}")
                # still persist webhook receipt but do not alter txn status
            else:
                if new_status and txn.status != new_status:
                    if txn.transaction_type == Transaction.TransactionType.TOP_UP and new_status == Transaction.TransactionStatus.COMPLETED:
                        # process the topup to credit wallet
                        try:
                            TransactionEngine.process(txn)
                        except Exception:
                            logger.exception("TransactionEngine.process failed while reconciling webhook (non-fatal)")
                    txn.status = new_status

            receipt = txn.receipt or {}
            receipt["last_webhook"] = sanitized_data
            txn.receipt = receipt
            txn.save(update_fields=["status", "receipt", "updated_at"])

    # ------------------- poll_transaction_status (instance-level helper) -------------------
    @staticmethod
    def poll_transaction_status(txn: Transaction, gateway_name: Optional[str] = None) -> str:
        """
        Poll status of a pending transaction from provider and reconcile.
        Useful as a fallback if webhook is missed.
        """
        if not gateway_name:
            gateway_name = (txn.receipt or {}).get("provider")
        if not gateway_name:
            raise ValidationError("Gateway name is required to poll transaction status")

        try:
            gw = get_gateway(gateway_name)
        except Exception as e:
            logger.exception("Failed to resolve gateway for polling")
            raise ValidationError(f"Gateway '{gateway_name}' not available")

        # many gateways accept client reference id / deposit id as single positional argument
        provider_key = getattr(txn, "idempotency_key", None) or (txn.receipt or {}).get("provider_id") or txn.reference
        if not provider_key:
            raise ValidationError("Transaction missing provider identifier (idempotency_key or receipt.provider_id)")

        # call provider check: we pass the provider_key as positional arg (gateway implementations should accept)
        try:
            resp = gw.check_transaction_status(provider_key)
        except TypeError:
            # some implementations expect a named parameter; attempt common param names
            try:
                resp = gw.check_transaction_status(client_reference_id=provider_key)
            except Exception as e:
                logger.exception("check_transaction_status invocation failed (unknown signature)")
                raise
        except Exception:
            logger.exception("Gateway check_transaction_status failed")
            raise

        sanitized = {}
        try:
            sanitized = PaymentService._validate_provider_response(
                resp,
                required_keys=["status"],
                gateway_name=gateway_name,
            )
            status = sanitized["status"].upper()
        except ValidationError:
            # if strict validation fails, try to read common fields
            status = (resp.get("status") or (resp.get("data") or {}).get("status") or "").upper()

        with db_txn.atomic():
            txn = Transaction.objects.select_for_update().get(pk=txn.pk)
            status_map = {
                "COMPLETED": Transaction.TransactionStatus.COMPLETED,
                "SUCCESS": Transaction.TransactionStatus.COMPLETED,
                "SUCCESSFUL": Transaction.TransactionStatus.COMPLETED,
                "FAILED": Transaction.TransactionStatus.FAILED,
                "REJECTED": Transaction.TransactionStatus.FAILED,
                "DECLINED": Transaction.TransactionStatus.FAILED,
            }
            new_status = status_map.get(status)
            if new_status and txn.status != new_status:
                if txn.transaction_type == Transaction.TransactionType.TOP_UP and new_status == Transaction.TransactionStatus.COMPLETED:
                    try:
                        TransactionEngine.process(txn)
                    except Exception:
                        logger.exception("TransactionEngine.process failed while polling (non-fatal)")
                txn.status = new_status

            receipt = txn.receipt or {}
            receipt["last_poll"] = resp
            txn.receipt = receipt
            txn.save(update_fields=["status", "receipt", "updated_at"])

        return txn.status