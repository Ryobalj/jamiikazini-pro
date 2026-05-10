# payments/views/payment_method_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payments.models.paymentmethod import PaymentMethod
from payments.serializers.paymentmethod_serializer import (
    PaymentMethodSerializer,
    PaymentMethodSummarySerializer,
)

class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    CRUD kwa Payment Methods za mtumiaji:
    - list: inarudisha summary (lite)
    - retrieve/create/update/delete: detailed
    - set-default: custom action
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        return PaymentMethod.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentMethodSummarySerializer
        return PaymentMethodSerializer

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        method = self.get_object()
        # Clear existing default first
        PaymentMethod.objects.filter(owner=request.user, is_default=True).update(is_default=False)
        method.is_default = True
        method.save(update_fields=["is_default"])

        return Response(
            {"detail": f"{method.method_type_display} imewekwa kama default."},
            status=status.HTTP_200_OK,
        )