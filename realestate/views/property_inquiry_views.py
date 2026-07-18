# realestate/views/property_inquiry_views.py

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from accounts.permissions import IsIdentityVerified
from realestate.models.property_listing import PropertyListing, PropertyStatus, PropertyListingType
from realestate.models.property_inquiry import PropertyInquiry, PropertyInquiryStatus
from realestate.serializers.property_inquiry_serializer import (
    PropertyInquirySerializer,
    PropertyInquiryCreateSerializer,
)
from jamiiwallet.services.escrow_hold_service import open_hold, capture_from_hold, void_remaining


class PropertyInquiryViewSet(viewsets.ModelViewSet):
    """
    Nia ya mnunuzi/mpangaji kwa tangazo fulani. `create` ni bure (hakuna
    malipo) - `reserve` ndiyo hatua inayoshikilia fedha (EscrowHold) na
    kuondoa tangazo kwenye orodha ya umma. `confirm-handover` inahitaji
    pande zote mbili kabla fedha kutolewa; `cancel` inarudisha fedha na
    tangazo kwenye AVAILABLE.
    """
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        # IsIdentityVerified ni lango la upande wa MNUNUZI pekee (create/reserve
        # ni matendo ya buyer). confirm-handover/cancel/incoming zinatumiwa na
        # mmiliki wa mali pia - biashara yake tayari ina uthibitisho wake
        # (Business.is_verified), asilazimishwe kuwa na NIDA ya kibinafsi
        # ili tu athibitishe amekabidhi/kughairi mali yake mwenyewe.
        if self.action in ("create", "reserve"):
            return [permissions.IsAuthenticated(), IsIdentityVerified()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return PropertyInquiryCreateSerializer
        return PropertyInquirySerializer

    def get_queryset(self):
        return PropertyInquiry.objects.filter(buyer=self.request.user).select_related(
            "property", "property__owner", "buyer"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            listing = PropertyListing.objects.get(pk=serializer.validated_data["property"])
        except PropertyListing.DoesNotExist:
            raise NotFound("Tangazo halipatikani.")
        if listing.status != PropertyStatus.AVAILABLE:
            raise ValidationError({"property": "Tangazo hili halipatikani tena."})

        inquiry = PropertyInquiry.objects.create(
            property=listing, buyer=request.user, message=serializer.validated_data.get("message", ""),
        )
        return Response(PropertyInquirySerializer(inquiry).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="incoming")
    def incoming(self, request):
        """Nia zilizopo kwa matangazo ya biashara za mtumiaji huyu."""
        qs = PropertyInquiry.objects.filter(
            property__owner__owner=request.user
        ).select_related("property", "property__owner", "buyer").order_by("-created_at")
        return Response(PropertyInquirySerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="reserve")
    @db_transaction.atomic
    def reserve(self, request, pk=None):
        inquiry = PropertyInquiry.objects.select_related("property").get(pk=pk)
        if inquiry.buyer_id != request.user.id:
            raise PermissionDenied("Huwezi kuchukua ombi hili.")
        if inquiry.status != PropertyInquiryStatus.PENDING:
            raise ValidationError({"detail": "Ombi hili si PENDING tena."})

        listing = PropertyListing.objects.select_for_update().get(pk=inquiry.property_id)
        if listing.status != PropertyStatus.AVAILABLE:
            raise ValidationError({"detail": "Tangazo hili halipatikani tena."})
        if not hasattr(request.user, "wallet"):
            raise ValidationError({"detail": "Wallet haipatikani."})

        try:
            eh = open_hold(
                request.user.wallet, listing.reservation_amount, initiated_by=request.user,
                linked_object=inquiry, idempotency_key=f"property-reserve-{inquiry.id}",
            )
        except DjangoValidationError:
            raise ValidationError({"detail": "Salio la JamiiWallet halitoshi kushikilia kiasi hiki."})

        inquiry.escrow_hold = eh
        inquiry.status = PropertyInquiryStatus.RESERVED
        inquiry.reserved_at = timezone.now()
        inquiry.save(update_fields=["escrow_hold", "status", "reserved_at", "updated_at"])

        listing.status = PropertyStatus.RESERVED
        listing.save(update_fields=["status", "updated_at"])

        # Nia nyingine za PENDING kwa tangazo hili hazina maana tena.
        PropertyInquiry.objects.filter(
            property=listing, status=PropertyInquiryStatus.PENDING
        ).exclude(pk=inquiry.pk).update(status=PropertyInquiryStatus.REJECTED, updated_at=timezone.now())

        return Response(PropertyInquirySerializer(inquiry).data)

    @action(detail=True, methods=["post"], url_path="confirm-handover")
    @db_transaction.atomic
    def confirm_handover(self, request, pk=None):
        inquiry = PropertyInquiry.objects.select_related("property", "property__owner").get(pk=pk)
        is_buyer = inquiry.buyer_id == request.user.id
        is_owner = inquiry.property.owner.owner_id == request.user.id
        if not (is_buyer or is_owner):
            raise PermissionDenied("Huna ruhusa kwa ombi hili.")
        if inquiry.status != PropertyInquiryStatus.RESERVED:
            raise ValidationError({"detail": "Ombi hili si RESERVED."})

        now = timezone.now()
        update_fields = ["updated_at"]
        if is_buyer and not inquiry.buyer_confirmed_at:
            inquiry.buyer_confirmed_at = now
            update_fields.append("buyer_confirmed_at")
        if is_owner and not inquiry.owner_confirmed_at:
            inquiry.owner_confirmed_at = now
            update_fields.append("owner_confirmed_at")

        if inquiry.is_handover_ready():
            listing = inquiry.property
            capture_from_hold(
                inquiry.escrow_hold, inquiry.escrow_hold.total_held,
                counterparty=listing.owner.owner, initiated_by=request.user,
                idempotency_key=f"property-handover-{inquiry.id}",
            )
            listing.status = (
                PropertyStatus.RENTED if listing.listing_type == PropertyListingType.RENT else PropertyStatus.SOLD
            )
            listing.save(update_fields=["status", "updated_at"])

            inquiry.status = PropertyInquiryStatus.COMPLETED
            inquiry.completed_at = now
            update_fields += ["status", "completed_at"]

        inquiry.save(update_fields=update_fields)
        return Response(PropertyInquirySerializer(inquiry).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    @db_transaction.atomic
    def cancel(self, request, pk=None):
        inquiry = PropertyInquiry.objects.select_related("property", "property__owner").get(pk=pk)
        is_buyer = inquiry.buyer_id == request.user.id
        is_owner = inquiry.property.owner.owner_id == request.user.id
        if not (is_buyer or is_owner):
            raise PermissionDenied("Huna ruhusa kwa ombi hili.")
        if inquiry.status not in (PropertyInquiryStatus.PENDING, PropertyInquiryStatus.RESERVED):
            raise ValidationError({"detail": "Ombi hili haliwezi kughairiwa tena."})

        if inquiry.escrow_hold:
            void_remaining(inquiry.escrow_hold, initiated_by=request.user, idempotency_key=f"property-cancel-{inquiry.id}")
            listing = PropertyListing.objects.select_for_update().get(pk=inquiry.property_id)
            if listing.status == PropertyStatus.RESERVED:
                listing.status = PropertyStatus.AVAILABLE
                listing.save(update_fields=["status", "updated_at"])

        inquiry.status = PropertyInquiryStatus.CANCELLED
        inquiry.cancelled_at = timezone.now()
        inquiry.save(update_fields=["status", "cancelled_at", "updated_at"])
        return Response(PropertyInquirySerializer(inquiry).data)
