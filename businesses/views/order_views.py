# businesses/views/order_views.py

from django.db import transaction
from rest_framework import viewsets, permissions, status as drf_status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from businesses.models.order import Order, PaymentMethod, PaymentStatus
from businesses.serializers.order_serializer import OrderSerializer
from security.decorators import conditional_2fa_required


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD kwa Orders.

    Rules:
    - Superuser anaona na kuhariri orders zote
    - Institution admin / Provider anaona na kuhariri orders za biashara zake pekee
    - Client anaona na kuhariri orders alizoanzisha
    - Admin actions zinaweza kuhitaji 2FA
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        business_id = self.kwargs.get("business_pk")

        if user.is_superuser:
            qs = Order.objects.filter(business_id=business_id) if business_id else Order.objects.all()
        elif user.role in ["INSTITUTION_ADMIN", "PROVIDER"]:
            qs = Order.objects.filter(business__owner=user)
            if business_id:
                qs = qs.filter(business_id=business_id)
        else:  # Client
            qs = Order.objects.filter(client=user)
            if business_id:
                qs = qs.filter(business_id=business_id)
        return qs

    def perform_create(self, serializer):
        """
        Ruhusu client au admin kuunda order.
        Client lazima awe ni request.user. Mnunuzi lazima awe amethibitisha
        kitambulisho chake (NIDA), na biashara analotununua kwake lazima
        iwe imethibitishwa rasmi - kuepuka manunuzi/mauzo bila uthibitisho.
        """
        user = self.request.user
        if not user.is_superuser and not user.is_identity_verified:
            raise PermissionDenied("Lazima uthibitishe kitambulisho chako (NIDA) kabla ya kununua.")

        business = serializer.validated_data.get("business")
        if business is not None and not business.is_verified:
            raise PermissionDenied("Biashara hii bado haijathibitishwa - manunuzi hayawezekani kwa sasa.")

        serializer.save(client=user)

    @conditional_2fa_required(action_type="admin_action")
    def perform_update(self, serializer):
        order = serializer.instance
        user = self.request.user

        if user.is_superuser:
            serializer.save()
        elif user.role in ["INSTITUTION_ADMIN", "PROVIDER"]:
            if order.business.owner != user:
                raise PermissionDenied("Huwezi kuhariri order isiyo ya biashara yako.")
            serializer.save()
        elif order.client == user:
            serializer.save()
        else:
            raise PermissionDenied("Huwezi kuhariri order isiyo yako.")

    @action(detail=True, methods=["post"], url_path="mark-cash-received")
    def mark_cash_received(self, request, pk=None):
        """
        Muuzaji anathibitisha kwamba amepokea fedha taslimu kwa oda ya CASH -
        hii ndiyo hatua pekee inayofunga malipo ya CASH_PENDING (hakuna wallet
        inayoguswa kabisa katika mtiririko huu).
        """
        order = self.get_object()
        if order.business.owner_id != request.user.id and not request.user.is_superuser:
            raise PermissionDenied("Huwezi kuthibitisha malipo ya oda isiyo ya biashara yako.")
        if order.payment_method != PaymentMethod.CASH:
            return Response(
                {"detail": "Oda hii si ya malipo taslimu."}, status=drf_status.HTTP_400_BAD_REQUEST
            )
        if order.payment_status != PaymentStatus.CASH_PENDING:
            return Response(
                {"detail": "Oda hii tayari imeshughulikiwa."}, status=drf_status.HTTP_400_BAD_REQUEST
            )
        order.payment_status = PaymentStatus.PAID
        order.save(update_fields=["payment_status"])
        return Response(OrderSerializer(order, context={"request": request}).data)

    @conditional_2fa_required(action_type="admin_action")
    def perform_destroy(self, instance):
        user = self.request.user

        if user.is_superuser:
            instance.delete()
        elif user.role in ["INSTITUTION_ADMIN", "PROVIDER"]:
            if instance.business.owner != user:
                raise PermissionDenied("Huwezi kufuta order isiyo ya biashara yako.")
            instance.delete()
        elif instance.client == user:
            instance.delete()
        else:
            raise PermissionDenied("Huwezi kufuta order isiyo yako.")


class BulkOrderCreateView(APIView):
    """
    Inaruhusu mnunuzi kuunda oda kadhaa (moja kwa kila muuzaji) kwa hatua moja -
    inatumika na kikapu chenye bidhaa za wauzaji wengi. Oda zote hutengenezwa
    ndani ya transaction moja: ikiwa oda moja itashindwa (mf. bidhaa
    haipatikani au biashara haijathibitishwa), hakuna oda yoyote itakayoundwa.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.is_superuser and not user.is_identity_verified:
            raise PermissionDenied("Lazima uthibitishe kitambulisho chako (NIDA) kabla ya kununua.")

        orders_data = request.data.get("orders")
        if not orders_data or not isinstance(orders_data, list):
            return Response({"detail": "Orodha ya 'orders' inahitajika."}, status=drf_status.HTTP_400_BAD_REQUEST)

        validated_serializers = []
        for order_data in orders_data:
            serializer = OrderSerializer(data=order_data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            business = serializer.validated_data.get("business")
            if business is not None and not business.is_verified:
                raise PermissionDenied(
                    f"Biashara '{business.name}' bado haijathibitishwa - manunuzi hayawezekani kwa sasa."
                )
            validated_serializers.append(serializer)

        created_orders = []
        with transaction.atomic():
            for serializer in validated_serializers:
                created_orders.append(serializer.save(client=user))

        return Response(
            {"orders": OrderSerializer(created_orders, many=True, context={"request": request}).data},
            status=drf_status.HTTP_201_CREATED,
        )