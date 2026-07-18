# logistics/views/fare_proposal_views.py

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from logistics.models.fare_proposal import FareProposal, FareProposalStatus
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_assignment import TransportAssignment
from logistics.choices import TransportRequestStatus
from logistics.serializers.fare_proposal_serializer import FareProposalSerializer


class FareProposalViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = FareProposalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Dereva anaona alizowasilisha yeye; mnunuzi anaona za maombi yake mwenyewe
        # (iwe kupitia order ya bidhaa au ombi la usafiri la moja kwa moja).
        from django.db.models import Q
        return FareProposal.objects.filter(
            Q(provider__user=user)
            | Q(transport_request__order__client=user)
            | Q(transport_request__requested_by=user)
        ).select_related("transport_request", "provider__user", "vehicle")

    @action(detail=True, methods=["post"], url_path="approve")
    @db_transaction.atomic
    def approve(self, request, pk=None):
        proposal = self.get_object()
        tr = proposal.transport_request
        is_owner = (
            (tr.order is not None and tr.order.client_id == request.user.id)
            or tr.requested_by_id == request.user.id
        )
        if not is_owner:
            raise PermissionDenied("Huwezi kuidhinisha pendekezo hili.")

        transport_request = TransportRequest.objects.select_for_update().get(pk=proposal.transport_request_id)
        if transport_request.status != TransportRequestStatus.PENDING:
            return Response(
                {"detail": "Ombi hili tayari limekubaliwa na dereva mwingine."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if proposal.status != FareProposalStatus.PENDING:
            return Response({"detail": "Pendekezo hili si tena la kusubiri."}, status=status.HTTP_400_BAD_REQUEST)

        from jamiiwallet.models.transaction import Transaction as WalletTransaction
        from jamiiwallet.services.transaction_engine import TransactionEngine

        order = None
        if transport_request.order_id:
            from businesses.models.order import Order
            order = Order.objects.select_for_update().get(pk=transport_request.order_id)
            payer_wallet, payer_user = order.client.wallet, order.client
            meta = {"order_id": str(order.id)}
        else:
            payer_wallet, payer_user = transport_request.requested_by.wallet, transport_request.requested_by
            meta = {"transport_request_id": str(transport_request.id)}

        estimated = transport_request.estimated_fare or Decimal("0")
        fare_diff = proposal.proposed_fare - estimated

        if fare_diff > 0:
            hold_txn = TransactionEngine.initiate(
                wallet=payer_wallet,
                amount=fare_diff,
                transaction_type=WalletTransaction.TransactionType.HOLD,
                initiated_by=payer_user,
                metadata={**meta, "purpose": "fare_diff"},
            )
            try:
                TransactionEngine.process(hold_txn)
            except DjangoValidationError:
                return Response(
                    {"detail": "Salio la JamiiWallet halitoshi kwa bei hii - ongeza salio kwanza."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif fare_diff < 0:
            void_txn = TransactionEngine.initiate(
                wallet=payer_wallet,
                amount=abs(fare_diff),
                transaction_type=WalletTransaction.TransactionType.VOID,
                initiated_by=payer_user,
                metadata={**meta, "purpose": "fare_diff_refund"},
            )
            TransactionEngine.process(void_txn)

        if order is not None:
            order.delivery_fee = order.delivery_fee + fare_diff
            order.total_amount = order.calculate_total()
            order.save(update_fields=["delivery_fee", "total_amount"])
        else:
            transport_request.estimated_fare = proposal.proposed_fare
            transport_request.save(update_fields=["estimated_fare"])

        assignment = TransportAssignment.objects.create(
            transport_request=transport_request,
            assigned_to=proposal.provider,
            vehicle=proposal.vehicle,
            agreed_fare=proposal.proposed_fare,
        )
        transport_request.status = TransportRequestStatus.ACCEPTED
        transport_request.is_accepted = True
        transport_request.save(update_fields=["status", "is_accepted"])

        proposal.status = FareProposalStatus.APPROVED
        proposal.save(update_fields=["status"])
        FareProposal.objects.filter(
            transport_request=transport_request, status=FareProposalStatus.PENDING
        ).exclude(pk=proposal.pk).update(status=FareProposalStatus.REJECTED)

        return Response({"assignment_id": str(assignment.pk), "agreed_fare": str(assignment.agreed_fare)})
