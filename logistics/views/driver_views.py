# logistics/views/driver.py

from rest_framework import viewsets
from logistics.permissions import IsProviderOwnerOrReadOnly
from logistics.models.driver import Driver
from logistics.serializers.driver_serializer import DriverSerializer


class DriverViewSet(viewsets.ModelViewSet):
    serializer_class = DriverSerializer
    permission_classes = [IsProviderOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return Driver.objects.all()
        return Driver.objects.filter(transport_provider__user=user)

    def perform_create(self, serializer):
        transport_provider = self.request.user.transportprovider
        serializer.save(transport_provider=transport_provider)