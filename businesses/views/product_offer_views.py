# businesses/views/product_offer_views.py

from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from businesses.models.product_offer import ProductOffer, ProductOfferStatus
from businesses.serializers.product_offer_serializer import (
    ProductOfferSerializer,
    ProductOfferRespondSerializer,
    ProductOfferBuyerDecisionSerializer,
)


class ProductOfferViewSet(viewsets.ModelViewSet):
    """
    Ofa za bei kwa bidhaa (kujadiliana bei) - mnunuzi anatoa ofa, muuzaji
    anakubali/anakataa/anatoa ofa mbadala, na ikiwa ofa mbadala mnunuzi
    anakubali/anakataa (duru moja tu, si majadiliano yasiyokwisha).
    """
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = ProductOfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # list/retrieve: mnunuzi anaona ofa zake mwenyewe pekee.
        return ProductOffer.objects.filter(buyer=self.request.user).select_related(
            "product", "product__business", "buyer"
        )

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_identity_verified:
            raise PermissionDenied("Lazima uthibitishe kitambulisho chako (NIDA) kabla ya kutoa ofa.")
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="incoming")
    def incoming(self, request):
        """Ofa zinazosubiri jibu la muuzaji, kwa bidhaa za biashara za mtumiaji huyu."""
        qs = ProductOffer.objects.filter(
            product__business__owner=request.user,
            status=ProductOfferStatus.PENDING,
        ).select_related("product", "product__business", "buyer").order_by("-created_at")
        return Response(ProductOfferSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="respond")
    @transaction.atomic
    def respond(self, request, pk=None):
        """Muuzaji anajibu ofa: ACCEPT / REJECT / COUNTER."""
        try:
            offer = ProductOffer.objects.select_for_update().select_related("product", "product__business").get(pk=pk)
        except ProductOffer.DoesNotExist:
            return Response({"detail": "Ofa hii haipatikani."}, status=status.HTTP_404_NOT_FOUND)

        if offer.product.business.owner_id != request.user.id:
            raise PermissionDenied("Huwezi kujibu ofa isiyo ya bidhaa yako.")
        if offer.status != ProductOfferStatus.PENDING:
            return Response({"detail": "Ofa hii tayari imeshughulikiwa."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductOfferRespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]

        if decision == "ACCEPT":
            offer.status = ProductOfferStatus.ACCEPTED
            offer.save(update_fields=["status"])
        elif decision == "REJECT":
            offer.status = ProductOfferStatus.REJECTED
            offer.save(update_fields=["status"])
        else:  # COUNTER
            offer.counter_unit_price = serializer.validated_data["counter_unit_price"]
            offer.status = ProductOfferStatus.COUNTERED
            offer.save(update_fields=["counter_unit_price", "status"])

        return Response(ProductOfferSerializer(offer).data)

    @action(detail=True, methods=["post"], url_path="decide")
    @transaction.atomic
    def decide(self, request, pk=None):
        """Mnunuzi anaamua kuhusu ofa mbadala ya muuzaji: ACCEPT / REJECT (mwisho)."""
        try:
            offer = ProductOffer.objects.select_for_update().get(pk=pk)
        except ProductOffer.DoesNotExist:
            return Response({"detail": "Ofa hii haipatikani."}, status=status.HTTP_404_NOT_FOUND)

        if offer.buyer_id != request.user.id:
            raise PermissionDenied("Huwezi kuamua kuhusu ofa isiyo yako.")
        if offer.status != ProductOfferStatus.COUNTERED:
            return Response({"detail": "Ofa hii haina ofa mbadala ya kuamua."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductOfferBuyerDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offer.status = (
            ProductOfferStatus.ACCEPTED if serializer.validated_data["decision"] == "ACCEPT"
            else ProductOfferStatus.REJECTED
        )
        offer.save(update_fields=["status"])
        return Response(ProductOfferSerializer(offer).data)
