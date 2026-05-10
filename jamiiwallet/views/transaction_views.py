# jamiiwallet/views/transaction_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.views import APIView

from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.serializers.transaction_serializer import TransactionSerializer
from kiini.permissions.wallet import IsTransactionOwnerOrInstitutionAdmin

from jamiiwallet.services.transaction_engine import TransactionEngine


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet ya kusoma transactions pekee. Uundaji unafanywa na system kupitia service layer.
    """
    queryset = Transaction.objects.select_related('wallet', 'counterparty', 'initiated_by')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTransactionOwnerOrInstitutionAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['transaction_type', 'status', 'wallet']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        return self.queryset.filter(wallet__user=user)

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Transactions must be initiated by the system, not directly via API."},
            status=status.HTTP_403_FORBIDDEN
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Transactions cannot be edited."},
            status=status.HTTP_403_FORBIDDEN
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Transactions cannot be deleted."},
            status=status.HTTP_403_FORBIDDEN
        )


class CreateTransactionAPIView(APIView):
    """
    API ya kuanzisha transaction mpya kwa kutumia TransactionEngine.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = TransactionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user

        # Anzisha transaction kupitia engine
        transaction = TransactionEngine.initiate(
            wallet=data.get("wallet"),
            amount=data.get("amount"),
            transaction_type=data.get("transaction_type"),
            initiated_by=user,
            counterparty=data.get("counterparty"),
            metadata=data.get("metadata"),
        )

        # Chakata transaction
        processed = TransactionEngine.process(transaction)

        response_serializer = TransactionSerializer(processed)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)