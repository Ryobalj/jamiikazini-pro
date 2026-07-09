# logistics/views/vehicle_views.py

from rest_framework import viewsets, permissions
from logistics.models import Vehicle
from logistics.serializers.vehicle_serializer import VehicleSerializer, VehicleWriteSerializer
from logistics.permissions import IsProviderOwnerOrReadOnly


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().select_related('provider', 'active_driver').prefetch_related('drivers')
    permission_classes = [permissions.IsAuthenticated, IsProviderOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return VehicleWriteSerializer
        return VehicleSerializer

    def perform_create(self, serializer):
        # Automatically assign current user's transport_provider
        transport_provider = self.request.user.transport_providers.first()
        serializer.save(provider=transport_provider)

    def perform_update(self, serializer):
        # Prevent provider change on update
        serializer.save()