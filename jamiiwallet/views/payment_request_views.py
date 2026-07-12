# jamiiwallet/views/payment_request_views.py

import logging

from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from jamiiwallet.models.payment_request import PaymentRequest
from jamiiwallet.serializers.payment_request_serializer import PaymentRequestSerializer

logger = logging.getLogger(__name__)


class PaymentRequestViewSet(viewsets.ModelViewSet):
    """
    'Omba Pesa': tengeneza ombi, ona maombi yako (uliyotuma na uliyopokea),
    kubali (huzalisha Transfer halisi) au kataa.
    """
    serializer_class = PaymentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        return (
            PaymentRequest.objects.filter(Q(requester=user) | Q(payer=user))
            .select_related('requester', 'payer')
        )

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        payment_request = self.get_object()
        if payment_request.payer_id != request.user.id:
            return Response(
                {'detail': 'Wewe si mlipaji wa ombi hili.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            payment_request.accept()
        except DjangoValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(payment_request).data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        payment_request = self.get_object()
        if payment_request.payer_id != request.user.id:
            return Response(
                {'detail': 'Wewe si mlipaji wa ombi hili.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            payment_request.decline()
        except DjangoValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(payment_request).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        payment_request = self.get_object()
        if payment_request.requester_id != request.user.id:
            return Response(
                {'detail': 'Wewe si muombaji wa ombi hili.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            payment_request.cancel()
        except DjangoValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(payment_request).data)
