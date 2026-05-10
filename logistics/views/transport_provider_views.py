# logistics/views/transport_provider_views.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from logistics.models import TransportProvider, TransportProviderVerification
from logistics.serializers.transport_provider_serializer import TransportProviderSerializer
from logistics.helpers.verification import (
    verify_nida,
    verify_driver_license,
    verify_business_license,
    verify_latra_license,
)


class TransportProviderViewSet(viewsets.ModelViewSet):
    queryset = TransportProvider.objects.all()
    serializer_class = TransportProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(institution=self.request.user.institution)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, institution=self.request.user.institution)

