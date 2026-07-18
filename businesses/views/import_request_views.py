# businesses/views/import_request_views.py

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from businesses.models.business import Business
from businesses.models.import_request import ImportRequest, ImportRequestStatus
from businesses.serializers.import_request_serializer import (
    ImportRequestSerializer,
    ImportRequestCreateSerializer,
    ImportRequestClaimSerializer,
)


class ImportRequestViewSet(viewsets.ModelViewSet):
    """
    Maombi ya uagizaji wa bidhaa kutoka nje (sourcing/quote-request). Mnunuzi
    anaunda ombi, biashara zenye deals_in_imports=True zinaona kwenye
    'incoming', na inayodai (claim) inatoa bei na makadirio ya siku.
    """
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ImportRequestCreateSerializer
        if self.action == "claim":
            return ImportRequestClaimSerializer
        return ImportRequestSerializer

    def get_queryset(self):
        # Mnunuzi anaona maombi yake mwenyewe pekee kupitia list/retrieve ya kawaida.
        return ImportRequest.objects.filter(buyer=self.request.user).select_related(
            "claimed_by_business", "budget_currency"
        )

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_identity_verified:
            raise PermissionDenied("Lazima uthibitishe kitambulisho chako (NIDA) kabla ya kuomba uagizaji.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        import_request = serializer.save()
        return Response(ImportRequestSerializer(import_request).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="incoming")
    def incoming(self, request):
        """Maombi ya uagizaji ambayo biashara za muagizaji huyu zinaweza kudai."""
        has_import_business = Business.objects.filter(
            owner=request.user, deals_in_imports=True, is_active=True
        ).exists()
        if not has_import_business:
            return Response([])

        qs = ImportRequest.objects.filter(
            status=ImportRequestStatus.PENDING
        ).select_related("budget_currency").order_by("-created_at")

        return Response(ImportRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="claim")
    @transaction.atomic
    def claim(self, request, pk=None):
        serializer = ImportRequestClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            import_request = ImportRequest.objects.select_for_update().get(
                pk=pk, status=ImportRequestStatus.PENDING
            )
        except ImportRequest.DoesNotExist:
            return Response(
                {"detail": "Ombi hili tayari limechukuliwa au halipo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            business = Business.objects.get(pk=data["business_id"])
        except Business.DoesNotExist:
            return Response({"detail": "Biashara haipatikani."}, status=status.HTTP_400_BAD_REQUEST)

        if business.owner_id != request.user.id:
            raise PermissionDenied("Huwezi kudai ombi kwa biashara isiyo yako.")

        if not business.deals_in_imports:
            return Response(
                {"detail": "Biashara yako haijajisajili kama muagizaji (deals in imports)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not business.is_verified:
            return Response(
                {"detail": "Biashara yako bado haijathibitishwa - huwezi kudai maombi ya uagizaji kwa sasa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Bei inahifadhiwa kwa sarafu ya msingi (TZS) - kama muagizaji amenukuu
        # kwa sarafu ya kigeni, tunabadilisha kwa exchange rate iliyopo.
        price = data["price"]
        currency_code = (data.get("currency_code") or "").strip().upper()
        if currency_code:
            from payments.services.currency_service import convert
            try:
                price = convert(price, currency_code)
            except Exception:
                return Response(
                    {"detail": f"Hakuna exchange rate ya {currency_code} kwa sasa - nukuu kwa TZS."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        import_request.status = ImportRequestStatus.CLAIMED
        import_request.claimed_by_business = business
        import_request.claimed_price = price
        import_request.estimated_lead_days = data["estimated_lead_days"]
        import_request.claimed_at = timezone.now()
        import_request.save(update_fields=[
            "status", "claimed_by_business", "claimed_price",
            "estimated_lead_days", "claimed_at",
        ])

        from kiini.helpers.notification_helper import notify_user
        notify_user(
            import_request.buyer,
            f"Ombi lako la uagizaji limekubaliwa na {business.name} - angalia bei na makadirio ya muda.",
        )

        return Response(ImportRequestSerializer(import_request).data)
