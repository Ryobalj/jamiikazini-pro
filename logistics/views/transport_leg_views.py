# logistics/views/transport_leg_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from logistics.models import TransportLeg, LegStatusLog
from logistics.serializers.transport_leg_serializer import TransportLegSerializer, LegStatusLogSerializer
from rest_framework.decorators import action
from kiini.helpers.domain import generate_subdomain_url


class TransportLegViewSet(viewsets.ModelViewSet):
    queryset = TransportLeg.objects.all().select_related('provider', 'shipment')
    serializer_class = TransportLegSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        leg = self.get_object()
        serializer = LegStatusLogSerializer(data=request.data)
        if serializer.is_valid():
            log = serializer.save(leg=leg, updated_by=request.user)
            leg.status = log.status
            leg.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Status updated successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def track_url(self, request, pk=None):
        leg = self.get_object()
        shipment = getattr(leg, 'shipment', None)
        sender = getattr(shipment, 'sender', None)
        institution = getattr(sender, 'institution', None)

        if institution and institution.slug:
            url = generate_subdomain_url(institution.slug, f"/track/shipment/{shipment.id}/")
            return Response({'track_url': url}, status=status.HTTP_200_OK)
        return Response({'detail': 'Sender institution slug not available'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def receiver_url(self, request, pk=None):
        leg = self.get_object()
        shipment = getattr(leg, 'shipment', None)
        receiver = getattr(shipment, 'receiver', None)
        institution = getattr(receiver, 'institution', None)

        if institution and institution.slug:
            url = generate_subdomain_url(institution.slug, f"/incoming/shipments/{shipment.id}/")
            return Response({'receiver_url': url}, status=status.HTTP_200_OK)
        return Response({'detail': 'Receiver institution slug not available'}, status=status.HTTP_400_BAD_REQUEST)


class LegStatusLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset ya kusoma status logs za leg fulani.
    """
    queryset = LegStatusLog.objects.all().select_related('leg', 'updated_by')
    serializer_class = LegStatusLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        leg_id = self.request.query_params.get('leg')
        if leg_id:
            queryset = queryset.filter(leg_id=leg_id)
        return queryset
