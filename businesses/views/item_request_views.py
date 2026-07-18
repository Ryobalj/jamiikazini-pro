# businesses/views/item_request_views.py

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from businesses.models.item_request import ItemRequest, ItemRequestStatus
from businesses.models.product import Product
from businesses.serializers.item_request_serializer import (
    ItemRequestSerializer,
    ItemRequestCreateSerializer,
    ItemRequestClaimSerializer,
)


class ItemRequestViewSet(viewsets.ModelViewSet):
    """
    Maombi ya bidhaa yanayotumwa (broadcast) kwa biashara za karibu. Mnunuzi
    anaunda ombi, biashara zenye bidhaa hiyo zinaona kwenye 'incoming', na
    ya kwanza kudai (claim) ndiyo inayomhudumia mnunuzi.
    """
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ItemRequestCreateSerializer
        if self.action == "claim":
            return ItemRequestClaimSerializer
        return ItemRequestSerializer

    def get_queryset(self):
        user = self.request.user
        # Mnunuzi anaona maombi yake mwenyewe pekee kupitia list/retrieve ya kawaida.
        return ItemRequest.objects.filter(buyer=user).select_related(
            "claimed_by_business", "claimed_product"
        )

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_identity_verified:
            raise PermissionDenied("Lazima uthibitishe kitambulisho chako (NIDA) kabla ya kuomba bidhaa.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item_request = serializer.save()
        return Response(ItemRequestSerializer(item_request).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="incoming")
    def incoming(self, request):
        """Maombi ambayo biashara za mtumiaji huyu zinaweza kuyahudumia."""
        my_product_ids = list(
            Product.objects.filter(business__owner=request.user).values_list("id", flat=True)
        )
        if not my_product_ids:
            return Response([])

        now = timezone.now()
        qs = ItemRequest.objects.filter(
            status=ItemRequestStatus.PENDING,
            matched_product_ids__overlap=my_product_ids,
        ).exclude(
            expires_at__lt=now
        ).order_by("-created_at")

        return Response(ItemRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="claim")
    @transaction.atomic
    def claim(self, request, pk=None):
        serializer = ItemRequestClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data["product_id"]

        try:
            item_request = ItemRequest.objects.select_for_update().get(
                pk=pk, status=ItemRequestStatus.PENDING
            )
        except ItemRequest.DoesNotExist:
            return Response(
                {"detail": "Ombi hili tayari limechukuliwa au halipo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item_request.expires_at and item_request.expires_at < timezone.now():
            item_request.status = ItemRequestStatus.EXPIRED
            item_request.save(update_fields=["status"])
            return Response({"detail": "Ombi hili limeisha muda wake."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.select_related("business").get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Bidhaa haipatikani."}, status=status.HTTP_400_BAD_REQUEST)

        if product.business.owner_id != request.user.id:
            raise PermissionDenied("Huwezi kudai ombi kwa bidhaa isiyo yako.")

        if not product.business.is_verified:
            return Response(
                {"detail": "Biashara yako bado haijathibitishwa - huwezi kudai maombi kwa sasa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if product.id not in (item_request.matched_product_ids or []):
            return Response(
                {"detail": "Bidhaa hii haikuwa sehemu ya waliolingana na ombi hili."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not product.is_available or product.quantity_in_stock < item_request.quantity:
            return Response({"detail": "Bidhaa hii haipatikani tena kwa kiasi kilichoombwa."}, status=status.HTTP_400_BAD_REQUEST)

        item_request.status = ItemRequestStatus.CLAIMED
        item_request.claimed_by_business = product.business
        item_request.claimed_product = product
        item_request.claimed_at = timezone.now()
        item_request.save(update_fields=["status", "claimed_by_business", "claimed_product", "claimed_at"])

        from kiini.helpers.notification_helper import notify_user
        notify_user(
            item_request.buyer,
            f"Ombi lako la '{item_request.product_name_query}' limekubaliwa na {product.business.name}.",
        )

        return Response(ItemRequestSerializer(item_request).data)
