# payments/views/invoice_views.py

from django.utils import timezone
from rest_framework.decorators import action
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
    queryset = Invoice.objects.select_related("user", "created_by", "last_modified_by")
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