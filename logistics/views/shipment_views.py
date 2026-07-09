# logistics/views/shipment_views.py

from rest_framework import viewsets, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from logistics.models.shipment import Shipment
from logistics.serializers.shipment_serializer import ShipmentSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from kiini.helpers.domain import generate_subdomain_url


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Only sender or receiver can modify the shipment.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.sender == request.user or obj.receiver == request.user


class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.select_related('sender', 'receiver', 'product')\
                               .prefetch_related('transport_providers')
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'tax_paid']
    search_fields = ['product__name', 'sender__email', 'receiver__email']
    ordering_fields = ['created_at', 'total_cost']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Shipment.objects.all()
        return Shipment.objects.filter(Q(sender=user) | Q(receiver=user))

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.total_cost = instance.transport_fee + instance.jamiikazini_commission
        instance.save(update_fields=['total_cost'])

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.total_cost = instance.transport_fee + instance.jamiikazini_commission
        instance.save(update_fields=['total_cost'])

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def sender_url(self, request, pk=None):
        shipment = self.get_object()
        sender = shipment.sender
        institution = getattr(sender, 'institution', None)
        if institution and institution.domain:
            url = generate_subdomain_url(institution.domain, f"/shipments/{shipment.id}/")
            return Response({'sender_url': url}, status=status.HTTP_200_OK)
        return Response({'detail': 'Sender institution slug not available'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def receiver_url(self, request, pk=None):
        shipment = self.get_object()
        receiver = shipment.receiver
        institution = getattr(receiver, 'institution', None)
        if institution and institution.domain:
            url = generate_subdomain_url(institution.domain, f"/incoming/shipments/{shipment.id}/")
            return Response({'receiver_url': url}, status=status.HTTP_200_OK)
        return Response({'detail': 'Receiver institution slug not available'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def transport_provider_url(self, request, pk=None):
        shipment = self.get_object()
        # Assuming shipment has a related transport_provider (single or first in m2m)
        provider = shipment.transport_providers.first()
        provider_institution = getattr(provider, 'institution', None) if provider else None
        if provider_institution and provider_institution.domain:
            url = generate_subdomain_url(provider_institution.domain, f"/dashboard/shipments/{shipment.id}/")
            return Response({'transport_provider_url': url}, status=status.HTTP_200_OK)
        return Response({'detail': 'Transport provider slug not available'}, status=status.HTTP_400_BAD_REQUEST)