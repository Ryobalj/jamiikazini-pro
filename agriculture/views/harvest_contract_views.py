# agriculture/views/harvest_contract_views.py

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from accounts.permissions import IsIdentityVerified
from businesses.models.business import Business
from agriculture.models.harvest_contract import HarvestContract, HarvestContractStatus
from agriculture.serializers.harvest_contract_serializer import (
    HarvestContractSerializer,
    HarvestContractCreateSerializer,
    HarvestContractClaimSerializer,
    HarvestContractDeliverySerializer,
)
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine
from jamiiwallet.services.escrow_hold_service import open_hold, capture_from_hold, void_remaining


class HarvestContractViewSet(viewsets.ModelViewSet):
    """
    Mkataba wa awali wa mazao - bei ya kila kilo imekubaliwa mapema, lakini
    malipo ya mwisho yanategemea uzito halisi uliopimwa wakati wa kupokea
    (dual-confirmation, sawa na delivery escrow iliyopo).
    """
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        # IsIdentityVerified ni lango la MNUNUZI pekee (create) - muuzaji
        # anatumia Business.is_verified badala ya NIDA ya kibinafsi.
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsIdentityVerified()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return HarvestContractCreateSerializer
        return HarvestContractSerializer

    def get_queryset(self):
        return HarvestContract.objects.filter(buyer=self.request.user).select_related("buyer", "seller")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = HarvestContract.objects.create(buyer=request.user, **serializer.validated_data)

        self._notify_agri_businesses()
        return Response(HarvestContractSerializer(contract).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _notify_agri_businesses():
        from kiini.helpers.notification_helper import notify_user

        notified_owners = set()
        sellers = Business.objects.filter(deals_in_agriculture=True, is_active=True).select_related("owner")
        for business in sellers:
            if business.owner_id in notified_owners:
                continue
            notified_owners.add(business.owner_id)
            notify_user(business.owner, "Kuna mkataba mpya wa mazao (harvest contract) kwenye Jamiikazini.")

    @action(detail=False, methods=["get"], url_path="incoming")
    def incoming(self, request):
        has_agri_business = Business.objects.filter(
            owner=request.user, deals_in_agriculture=True, is_active=True
        ).exists()
        if not has_agri_business:
            return Response([])

        qs = HarvestContract.objects.filter(
            status=HarvestContractStatus.PENDING
        ).select_related("buyer").order_by("-created_at")
        return Response(HarvestContractSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="claim")
    @db_transaction.atomic
    def claim(self, request, pk=None):
        serializer = HarvestContractClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract = HarvestContract.objects.select_for_update().get(pk=pk)
        if contract.status != HarvestContractStatus.PENDING:
            raise ValidationError({"detail": "Mkataba huu tayari umedaiwa au haupatikani."})

        try:
            business = Business.objects.get(pk=serializer.validated_data["business_id"])
        except Business.DoesNotExist:
            raise NotFound("Biashara haipatikani.")
        if business.owner_id != request.user.id:
            raise PermissionDenied("Huwezi kudai mkataba kwa biashara isiyo yako.")
        if not business.deals_in_agriculture:
            raise ValidationError({"detail": "Biashara yako haijajisajili kama muuzaji wa mazao."})
        if not business.is_verified:
            raise PermissionDenied("Biashara yako bado haijathibitishwa - huwezi kudai mikataba kwa sasa.")

        buyer = contract.buyer
        if not hasattr(buyer, "wallet"):
            raise ValidationError({"detail": "Wallet ya mnunuzi haipatikani."})

        try:
            eh = open_hold(
                buyer.wallet, contract.deposit_amount, initiated_by=request.user,
                linked_object=contract, idempotency_key=f"harvest-deposit-{contract.id}",
            )
        except DjangoValidationError:
            raise ValidationError({"detail": "Salio la mnunuzi halitoshi kushikilia amana ya mkataba huu."})

        contract.seller = business
        contract.escrow_hold = eh
        contract.status = HarvestContractStatus.ACCEPTED
        contract.save(update_fields=["seller", "escrow_hold", "status", "updated_at"])

        return Response(HarvestContractSerializer(contract).data)

    @action(detail=True, methods=["post"], url_path="confirm-delivery")
    @db_transaction.atomic
    def confirm_delivery(self, request, pk=None):
        serializer = HarvestContractDeliverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delivered_weight = serializer.validated_data["delivered_weight_kg"]

        # select_related("seller") kwenye select_for_update() ingesababisha
        # "FOR UPDATE cannot be applied to the nullable side of an outer join"
        # kwenye PostgreSQL, kwa sababu `seller` ni FK inayoruhusu null - kwa
        # hiyo tunapachika lock kwenye jedwali kuu pekee, kisha tunapata
        # buyer/seller kupitia query tofauti (bei ndogo ya ziada, salama).
        contract = HarvestContract.objects.select_for_update().get(pk=pk)
        is_buyer = contract.buyer_id == request.user.id
        is_seller = contract.seller_id and contract.seller.owner_id == request.user.id
        if not (is_buyer or is_seller):
            raise PermissionDenied("Huna ruhusa kwa mkataba huu.")
        if contract.status != HarvestContractStatus.ACCEPTED:
            raise ValidationError({"detail": "Mkataba huu si ACCEPTED."})

        now = timezone.now()
        update_fields = ["updated_at"]
        if is_buyer:
            contract.buyer_confirmed_weight = delivered_weight
            contract.buyer_confirmed_at = now
            update_fields += ["buyer_confirmed_weight", "buyer_confirmed_at"]
        if is_seller:
            contract.seller_confirmed_weight = delivered_weight
            contract.seller_confirmed_at = now
            update_fields += ["seller_confirmed_weight", "seller_confirmed_at"]

        if contract.both_weights_confirmed():
            if contract.weights_match_within_tolerance():
                average_weight = (contract.buyer_confirmed_weight + contract.seller_confirmed_weight) / Decimal("2")
                final_amount = (average_weight * contract.agreed_price_per_kg).quantize(Decimal("0.01"))
                eh = contract.escrow_hold

                capture_from_hold(
                    eh, min(final_amount, eh.remaining), counterparty=contract.seller.owner,
                    initiated_by=request.user, idempotency_key=f"harvest-capture-{contract.id}",
                )

                extra = final_amount - eh.total_held
                if extra > 0:
                    try:
                        extra_txn = TransactionEngine.initiate(
                            wallet=contract.buyer.wallet, amount=extra,
                            transaction_type=Transaction.TransactionType.PAYMENT,
                            initiated_by=request.user, counterparty=contract.seller.owner,
                            idempotency_key=f"harvest-extra-payment-{contract.id}",
                        )
                        TransactionEngine.process(extra_txn)
                    except DjangoValidationError:
                        raise ValidationError({
                            "detail": "Uzito uliopokewa umezidi makadirio - salio la mnunuzi halitoshi kulipa ziada."
                        })
                elif extra < 0:
                    void_remaining(eh, initiated_by=request.user, idempotency_key=f"harvest-void-{contract.id}")

                contract.status = HarvestContractStatus.SETTLED
                contract.settled_at = now
                update_fields += ["status", "settled_at"]
            else:
                contract.status = HarvestContractStatus.DISPUTED
                update_fields.append("status")

        contract.save(update_fields=update_fields)
        return Response(HarvestContractSerializer(contract).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    @db_transaction.atomic
    def cancel(self, request, pk=None):
        contract = HarvestContract.objects.select_for_update().get(pk=pk)
        is_buyer = contract.buyer_id == request.user.id
        is_seller = contract.seller_id and contract.seller.owner_id == request.user.id
        if not (is_buyer or is_seller):
            raise PermissionDenied("Huna ruhusa kwa mkataba huu.")
        if contract.status not in (HarvestContractStatus.PENDING, HarvestContractStatus.ACCEPTED):
            raise ValidationError({"detail": "Mkataba huu hauwezi kughairiwa tena."})

        if contract.escrow_hold:
            void_remaining(contract.escrow_hold, initiated_by=request.user, idempotency_key=f"harvest-cancel-{contract.id}")

        contract.status = HarvestContractStatus.CANCELLED
        contract.cancelled_at = timezone.now()
        contract.save(update_fields=["status", "cancelled_at", "updated_at"])
        return Response(HarvestContractSerializer(contract).data)
