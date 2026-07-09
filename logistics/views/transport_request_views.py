# logistics/views/transport_request_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from logistics.models import TransportRequest
from logistics.serializers.transport_request_serializers import (
    TransportRequestSerializer,
    TransportRequestWriteSerializer,
    RecommendedVehicleSerializer
)
from logistics.permissions import IsInstitutionOrBusiness
from logistics.models import Vehicle


class TransportRequestViewSet(viewsets.ModelViewSet):
    queryset = TransportRequest.objects.all().select_related("business", "institution")

    def get_queryset(self):
        # Multi-tenancy: users only see requests from their own institution
        # or their own businesses; staff see everything.
        from django.db.models import Q
        user = self.request.user
        qs = TransportRequest.objects.all().select_related("business", "institution")
        if user.is_superuser or user.is_staff:
            return qs
        filters = Q(pk=None)
        if getattr(user, "institution_id", None):
            filters |= Q(institution_id=user.institution_id)
        filters |= Q(business__owner=user)
        return qs.filter(filters)
    permission_classes = [permissions.IsAuthenticated, IsInstitutionOrBusiness]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TransportRequestWriteSerializer
        return TransportRequestSerializer

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError as DRFValidationError
        user = self.request.user
        business = user.businesses.first() if hasattr(user, "businesses") else None
        if business is not None:
            serializer.save(requestor_type="business", business=business)
        elif getattr(user, "institution", None) is not None:
            serializer.save(requestor_type="institution", institution=user.institution)
        else:
            raise DRFValidationError(
                "User must be associated with a business or institution."
            )

    @action(detail=True, methods=["get"], url_path="recommended-vehicles")
    def recommended_vehicles(self, request, pk=None):
        transport_request = self.get_object()
        recommended = transport_request.get_recommended_vehicles()
        serializer = RecommendedVehicleSerializer(recommended, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
