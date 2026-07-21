# logistics/views/transport_request_views.py

from django.contrib.gis.db.models.functions import Distance
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from logistics.models import TransportRequest
from logistics.choices import TransportRequestStatus
from logistics.serializers.transport_request_serializers import (
    TransportRequestSerializer,
    TransportRequestWriteSerializer,
    RecommendedVehicleSerializer
)
from logistics.permissions import IsTransporterOrAdmin
from logistics.models import Vehicle


class TransportRequestViewSet(viewsets.ModelViewSet):
    queryset = TransportRequest.objects.all().select_related("business", "institution")

    def get_queryset(self):
        # Multi-tenancy: users only see requests from their own institution,
        # their own businesses, or standalone requests they made themselves;
        # staff see everything.
        from django.db.models import Q
        user = self.request.user
        qs = TransportRequest.objects.all().select_related("business", "institution")
        if user.is_superuser or user.is_staff:
            return qs
        filters = Q(pk=None)
        if getattr(user, "institution_id", None):
            filters |= Q(institution_id=user.institution_id)
        filters |= Q(business__owner=user)
        filters |= Q(requested_by=user)
        return qs.filter(filters)
    # Kila mtumiaji aliye-login anaweza kuomba huduma ya usafiri moja kwa moja
    # (requestor_type="individual") - get_queryset() ndiyo inayolinda ni nani
    # anaona ombi gani, si role hapa.
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == "available":
            return [permissions.IsAuthenticated(), IsTransporterOrAdmin()]
        if self.action in ("fare_proposals", "by_order"):
            # Ruhusa ya kina inashughulikiwa ndani ya action yenyewe (lazima
            # awe ndiye client wa order husika) - si owner wa biashara/taasisi.
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TransportRequestWriteSerializer
        return TransportRequestSerializer

    @staticmethod
    def _remember_last_dropoff(user, serializer):
        # Save the drop-off used on this request as the user's "last address"
        # so RequestServicePage can pre-fill it for them next time, regardless
        # of which requestor_type branch created the request.
        dropoff = serializer.validated_data.get("dropoff_location")
        if dropoff is None:
            return
        user.last_dropoff_lat = dropoff.y
        user.last_dropoff_lng = dropoff.x
        user.last_dropoff_address_text = serializer.validated_data.get("dropoff_address_text", "") or ""
        user.save(update_fields=["last_dropoff_lat", "last_dropoff_lng", "last_dropoff_address_text"])

    def perform_create(self, serializer):
        from decimal import Decimal
        from django.core.exceptions import ValidationError as DjangoValidationError
        from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied

        user = self.request.user
        business = user.businesses.first() if hasattr(user, "businesses") else None
        if business is not None:
            serializer.save(requestor_type="business", business=business)
            self._remember_last_dropoff(user, serializer)
            return
        if getattr(user, "institution", None) is not None:
            serializer.save(requestor_type="institution", institution=user.institution)
            self._remember_last_dropoff(user, serializer)
            return

        # Standalone request: a plain buyer wants pure transport (no product
        # order behind it) - e.g. "I need a boda-boda from A to B right now".
        # Unlike a product order (where the delivery fee rides along with the
        # product total), there's no other payment step to piggyback on here,
        # so the estimated fare is held directly from the requester's wallet
        # at creation time - mirroring _create_delivery()'s hold-then-create
        # ordering in businesses/serializers/order_serializer.py.
        if not user.is_superuser and not user.is_identity_verified:
            raise PermissionDenied("Lazima uthibitishe kitambulisho chako kabla ya kuomba huduma ya usafiri.")

        from logistics.models.rate_card import TransportRateCard
        from logistics.services.weight_bands import is_vehicle_suitable
        from jamiiwallet.models.transaction import Transaction as WalletTransaction
        from jamiiwallet.services.transaction_engine import TransactionEngine

        vehicle_type = serializer.validated_data.get("suggested_transport_type")
        if not vehicle_type:
            raise DRFValidationError(
                {"suggested_transport_type": "Chagua aina ya usafiri kutoka kwenye orodha ya bei."}
            )

        pickup = serializer.validated_data["pickup_location"]
        dropoff = serializer.validated_data["dropoff_location"]
        weight_kg = serializer.validated_data.get("weight_kg") or 5.0
        volume_cbm = serializer.validated_data.get("volume_cbm")
        distance_km = pickup.distance(dropoff) * 100  # deg -> approx km

        if not is_vehicle_suitable(vehicle_type, weight_kg, distance_km, volume_cbm):
            raise DRFValidationError(
                {"suggested_transport_type": "Aina hii ya usafiri haifai kwa uzito/umbali wa mzigo huu."}
            )
        try:
            rate_card = TransportRateCard.objects.get(vehicle_type=vehicle_type, is_active=True)
        except TransportRateCard.DoesNotExist:
            raise DRFValidationError({"suggested_transport_type": "Aina hii ya usafiri haipatikani kwa sasa."})

        fare = rate_card.estimate_fare(distance_km, weight_kg)

        hold_txn = TransactionEngine.initiate(
            wallet=user.wallet,
            amount=fare,
            transaction_type=WalletTransaction.TransactionType.HOLD,
            initiated_by=user,
            metadata={"purpose": "standalone_transport_fare"},
        )
        try:
            TransactionEngine.process(hold_txn)
        except DjangoValidationError:
            raise DRFValidationError(
                {"payment": "Salio la JamiiWallet halitoshi kulipia huduma hii ya usafiri."}
            )

        serializer.save(requestor_type="individual", requested_by=user, estimated_fare=fare)
        self._remember_last_dropoff(user, serializer)

    @action(detail=True, methods=["get"], url_path="recommended-vehicles")
    def recommended_vehicles(self, request, pk=None):
        transport_request = self.get_object()
        recommended = transport_request.get_recommended_vehicles()
        serializer = RecommendedVehicleSerializer(recommended, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="available")
    def available(self, request):
        """
        Kazi za usafiri zilizo wazi (PENDING, hazijapewa dereva) karibu na dereva
        huyu, zinazolingana na aina za magari anazomiliki. Haihusiani na
        get_queryset() ya kawaida (ambayo ni ya wamiliki wa biashara/taasisi).
        """
        driver_vehicle_types = list(
            Vehicle.objects.filter(
                provider__user=request.user, is_active=True
            ).values_list("vehicle_type", flat=True).distinct()
        )
        if not driver_vehicle_types:
            return Response([])

        provider = request.user.transport_providers.first()
        qs = TransportRequest.objects.filter(
            status=TransportRequestStatus.PENDING,
            transportassignment__isnull=True,
            suggested_transport_type__in=driver_vehicle_types,
        ).select_related("business", "order")

        if provider and provider.location:
            max_distance_km = int(request.query_params.get("radius_km", 50))
            qs = qs.annotate(
                distance=Distance("pickup_location", provider.location)
            ).filter(distance__lte=max_distance_km * 1000).order_by("distance")
        else:
            qs = qs.order_by("requested_at")

        serializer = TransportRequestSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="fare-proposals")
    def fare_proposals(self, request, pk=None):
        from rest_framework.exceptions import PermissionDenied
        from logistics.serializers.fare_proposal_serializer import FareProposalSerializer

        transport_request = TransportRequest.objects.select_related("order").get(pk=pk)
        is_owner = (
            (transport_request.order is not None and transport_request.order.client_id == request.user.id)
            or transport_request.requested_by_id == request.user.id
        )
        if not is_owner:
            raise PermissionDenied("Huwezi kuona mapendekezo ya ombi hili.")

        proposals = transport_request.fare_proposals.select_related("provider__user", "vehicle")
        return Response(FareProposalSerializer(proposals, many=True).data)

    @action(detail=False, methods=["get"], url_path="by-order/(?P<order_id>[^/.]+)")
    def by_order(self, request, order_id=None):
        from rest_framework.exceptions import PermissionDenied

        try:
            transport_request = TransportRequest.objects.select_related(
                "order", "transportassignment", "transportassignment__vehicle", "transportassignment__assigned_to__user"
            ).get(order_id=order_id)
        except TransportRequest.DoesNotExist:
            return Response(None)

        if transport_request.order is None or transport_request.order.client_id != request.user.id:
            raise PermissionDenied("Huwezi kuona ombi hili la usafiri.")

        serializer = TransportRequestSerializer(transport_request, context={"request": request})
        return Response(serializer.data)
