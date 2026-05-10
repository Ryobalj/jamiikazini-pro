# payments/views/payment_method_api.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from payments.models.paymentmethod import PaymentMethod
from payments.models.invoice import Invoice
from payments.services.payment_service import PaymentService
from security.helpers.payment_otp import enforce_high_value_otp


class PaymentViewSet(viewsets.ViewSet):
    """
    Endpoint ya malipo:
    - POST /pay-invoice/ inachukua invoice_id na payment_method_id
    - Malipo husindika kupitia PaymentService (Wallet, Card, Bank, MNO, etc.)
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="pay-invoice")
    def pay_invoice(self, request):
        user = request.user
        invoice_id = request.data.get("invoice_id")
        payment_method_id = request.data.get("payment_method_id")

        # Validate invoice & payment method
        invoice = self._get_invoice(invoice_id, user)
        payment_method = self._get_payment_method(payment_method_id, user)

        # 🔐 Enforce OTP kwa high-value payments
        try:
            enforce_high_value_otp(request, user, invoice.total_amount)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        # Dispatch kwa service layer
        try:
            txn = PaymentService.process_payment(
                user=user,
                invoice=invoice,
                payment_method=payment_method
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NotImplementedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)

        return Response({
            "transaction_id": txn.reference,   # standardized identifier
            "invoice_id": str(invoice.id),
            "amount": str(txn.amount),
            "status": "success"
        }, status=status.HTTP_200_OK)

    def _get_invoice(self, invoice_id, user):
        try:
            return Invoice.objects.get(id=invoice_id, user=user)
        except Invoice.DoesNotExist:
            raise ValidationError("Invoice haipo au haikuhusiana na mtumiaji.")

    def _get_payment_method(self, payment_method_id, user):
        try:
            return PaymentMethod.objects.get(id=payment_method_id, owner=user)
        except PaymentMethod.DoesNotExist:
            raise ValidationError("Payment method haipo au haikuhusiana na mtumiaji.")
