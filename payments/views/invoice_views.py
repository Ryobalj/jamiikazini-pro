# payments/views/invoice_views.py

from decimal import Decimal
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import status as drf_status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from payments.models.invoice import Invoice, InvoiceStatus
from payments.serializers.invoice_serializer import InvoiceSerializer
from payments.views.base import BaseCRUDViewSet
from payments.models.audit_log import AuditLog, AuditAction


class InvoiceViewSet(BaseCRUDViewSet):
    """
    CRUD ViewSet kwa Invoice.
    - User, created_by, na last_modified_by huwekwa automatically.
    - invoice_number na total_amount huchaguliwa ki-automatic na model.
    """
    queryset = Invoice.objects.select_related("user", "created_by", "last_modified_by", "b2b_order", "b2b_order__business", "b2b_order__purchasing_business")
    serializer_class = InvoiceSerializer
    # Invoice ina field 'user' (si 'owner' - default ya BaseCRUDViewSet), hivyo
    # bila hii auto-scoping ya BaseCRUDViewSet.get_queryset() haiwezi kutambua
    # field sahihi na ingerudisha invoices ZA WATUMIAJI WOTE kwa mtu yeyote.
    owner_field = "user"
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        invoice = serializer.save(
            user=self.request.user,
            created_by=self.request.user,
            last_modified_by=self.request.user,
        )
        # Audit log: Invoice created
        AuditLog.log_from_request(
            self.request,
            user=self.request.user,
            action=AuditAction.CREATE,
            description=f"Invoice {invoice.id} created",
            metadata={
                "invoice_id": str(invoice.id),
                "status": invoice.status,
                "amount": str(invoice.total_amount),
                "currency": invoice.currency,
            },
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        old_status = instance.status
        invoice = serializer.save(last_modified_by=self.request.user)

        # Audit log: status change only
        if old_status != invoice.status:
            AuditLog.log_from_request(
                self.request,
                user=self.request.user,
                action=AuditAction.INVOICE_STATUS_CHANGE,
                description=f"Invoice {invoice.id} status changed {old_status} → {invoice.status}",
                metadata={
                    "invoice_id": str(invoice.id),
                    "old_status": old_status,
                    "new_status": invoice.status,
                    "amount": str(invoice.total_amount),
                    "currency": invoice.currency,
                },
            )

    @action(detail=True, methods=["post"], url_path="pay")
    @db_transaction.atomic
    def pay(self, request, pk=None):
        """
        Mnunuzi (biashara yenye mkopo) analipa invoice yake mwenyewe kupitia
        JamiiWallet - kinyume na mark-paid (ambayo ni admin override isiyohamisha
        fedha), hii ndiyo inayofanya uhamishaji halisi wa fedha kutoka wallet ya
        mnunuzi kwenda ya muuzaji, kisha inapunguza outstanding_credit ya
        BusinessCreditAccount husika.
        """
        invoice = self.get_object()
        if invoice.user_id != request.user.id and not request.user.is_superuser:
            raise PermissionDenied("Huwezi kulipa invoice isiyo yako.")
        if invoice.status == InvoiceStatus.PAID:
            return Response({"detail": "Invoice tayari imelipwa."}, status=drf_status.HTTP_400_BAD_REQUEST)

        order = getattr(invoice, "b2b_order", None)
        if order is None:
            return Response(
                {"detail": "Invoice hii haihusiani na oda ya B2B - tumia mark-paid badala yake."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        from businesses.models.business_credit_account import BusinessCreditAccount
        from jamiiwallet.models.transaction import Transaction as WalletTransaction
        from jamiiwallet.services.transaction_engine import TransactionEngine

        payer_wallet = getattr(invoice.user, "wallet", None)
        merchant_wallet = getattr(order.business.owner, "wallet", None)
        if not payer_wallet or not merchant_wallet:
            return Response(
                {"detail": "Wallet haipatikani kwa mmoja wa wahusika."}, status=drf_status.HTTP_400_BAD_REQUEST
            )

        payment_txn = TransactionEngine.initiate(
            wallet=payer_wallet,
            amount=invoice.total_amount,
            transaction_type=WalletTransaction.TransactionType.PAYMENT,
            initiated_by=invoice.user,
            counterparty=order.business.owner,
            metadata={"invoice_id": str(invoice.id), "order_id": str(order.id), "purpose": "b2b_invoice"},
        )
        try:
            TransactionEngine.process(payment_txn)
        except DjangoValidationError:
            return Response(
                {"detail": "Salio la JamiiWallet halitoshi kulipia invoice hii."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        invoice.mark_as_paid()

        try:
            credit_account = BusinessCreditAccount.objects.select_for_update().get(
                business=order.purchasing_business
            )
            credit_account.outstanding_credit = max(
                Decimal("0.00"), credit_account.outstanding_credit - invoice.total_amount
            )
            credit_account.save(update_fields=["outstanding_credit"])
        except BusinessCreditAccount.DoesNotExist:
            pass

        AuditLog.log_from_request(
            request, user=request.user, action=AuditAction.INVOICE_STATUS_CHANGE,
            description=f"Invoice {invoice.id} paid via wallet by {request.user.email}",
            metadata={"invoice_id": str(invoice.id), "amount": str(invoice.total_amount)},
        )

        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        """
        Custom action: kuweka invoice kama imelipwa.
        """
        invoice = self.get_object()
        if invoice.status == InvoiceStatus.PAID:
            return Response({"detail": "Invoice tayari imelipwa."}, status=400)

        old_status = invoice.status
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = timezone.now()
        invoice.last_modified_by = request.user
        invoice.save()

        # Audit log: mark paid
        AuditLog.log_from_request(
            request,
            user=request.user,
            action=AuditAction.INVOICE_STATUS_CHANGE,
            description=f"Invoice {invoice.id} status changed {old_status} → {invoice.status}",
            metadata={
                "invoice_id": str(invoice.id),
                "old_status": old_status,
                "new_status": invoice.status,
                "amount": str(invoice.total_amount),
            },
        )

        return Response(self.get_serializer(invoice).data)