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
    permission_classes = [permissions.IsAuthenticated, IsInstitutionOrBusiness]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TransportRequestWriteSerializer
        return TransportRequestSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'business'):
            serializer.save(requestor_type='business', business=user.business)
        elif hasattr(user, 'institution'):
            serializer.save(requestor_type='institution', institution=user.institution)
        else:
            raise ValueError("User must be associated with a business or institution.")

    @action(detail=True, methods=["get"], url_path="recommended-vehicles")
    def recommended_vehicles(self, request, pk=None):
        transport_request = self.get_object()
        recommended = transport_request.get_recommended_vehicles()
        serializer = RecommendedVehicleSerializer(recommended, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
