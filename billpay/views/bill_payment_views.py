# billpay/views/bill_payment_views.py

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from accounts.permissions import IsIdentityVerified
from billpay.models.bill_payment import BillPayment, BillPaymentStatus
from billpay.models.biller import Biller
from billpay.serializers.bill_payment_serializer import (
    BillerSerializer,
    BillPaymentSerializer,
    BillPaymentCreateSerializer,
)
from billpay.helpers.biller_api import purchase
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine
from security.helpers.payment_otp import enforce_high_value_otp


class BillerViewSet(viewsets.ReadOnlyModelViewSet):
    """Orodha ya wauzaji wa huduma wanaopatikana - kusoma tu, umma."""
    queryset = Biller.objects.filter(is_active=True).select_related("country")
    serializer_class = BillerSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["category", "country"]


class BillPaymentViewSet(viewsets.ModelViewSet):
    """
    Malipo ya huduma (LUKU, airtime, DSTV, maji). Fedha zinatolewa kwenye wallet
    kama WITHDRAWAL (zinatoka kabisa nje ya Jamiikazini) - biller API ikishindwa
    baada ya kutolewa, tunazirudisha kwa REFUND moja kwa moja.
    """
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [permissions.IsAuthenticated, IsIdentityVerified]

    def get_queryset(self):
        return BillPayment.objects.filter(user=self.request.user).select_related("biller", "currency")

    def get_serializer_class(self):
        if self.action == "create":
            return BillPaymentCreateSerializer
        return BillPaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        biller = serializer.validated_data["biller"]
        account_number = serializer.validated_data["account_number"]
        amount = serializer.validated_data["amount"]

        user = request.user
        if not hasattr(user, "wallet"):
            return Response({"detail": "Wallet haipatikani."}, status=status.HTTP_400_BAD_REQUEST)

        enforce_high_value_otp(request, user, amount, currency=user.wallet.currency.code)

        bill_payment = BillPayment.objects.create(
            user=user, biller=biller, account_number=account_number,
            amount=amount, currency=user.wallet.currency,
        )

        txn = TransactionEngine.initiate(
            wallet=user.wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            initiated_by=user,
            idempotency_key=f"billpay-{bill_payment.id}",
            metadata={"bill_payment_id": str(bill_payment.id), "biller": biller.name},
        )
        try:
            TransactionEngine.process(txn)
        except DjangoValidationError as e:
            bill_payment.status = BillPaymentStatus.FAILED
            bill_payment.response_data = {"error": str(e)}
            bill_payment.save(update_fields=["status", "response_data", "updated_at"])
            return Response({"detail": "Salio la JamiiWallet halitoshi."}, status=status.HTTP_400_BAD_REQUEST)

        bill_payment.wallet_transaction = txn
        bill_payment.save(update_fields=["wallet_transaction", "updated_at"])

        result = purchase(biller, account_number, amount)

        if result.get("status") == "success":
            bill_payment.status = BillPaymentStatus.COMPLETED
            bill_payment.external_reference = result.get("external_reference", "")
            bill_payment.response_data = result
            if result.get("token"):
                bill_payment.token_or_receipt = result["token"]
            bill_payment.save()
            return Response(BillPaymentSerializer(bill_payment).data, status=status.HTTP_201_CREATED)

        # Biller ilishindwa BAADA ya wallet kutozwa - rudisha fedha mara moja.
        refund_txn = TransactionEngine.initiate(
            wallet=user.wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.REFUND,
            initiated_by=user,
            idempotency_key=f"billpay-refund-{bill_payment.id}",
            metadata={"source_txn_id": str(txn.id), "bill_payment_id": str(bill_payment.id)},
        )
        TransactionEngine.process(refund_txn)

        bill_payment.status = BillPaymentStatus.FAILED
        bill_payment.response_data = result
        bill_payment.save()

        return Response(
            {"detail": result.get("error", "Malipo yameshindwa. Fedha zimerudishwa kwenye wallet yako.")},
            status=status.HTTP_502_BAD_GATEWAY,
        )
