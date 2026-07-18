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
        from django.db.models import Q
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return self.queryset
        filters = Q(user=user)
        if getattr(user, "institution_id", None):
            filters |= Q(institution_id=user.institution_id)
        return self.queryset.filter(filters)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, institution=self.request.user.institution)

