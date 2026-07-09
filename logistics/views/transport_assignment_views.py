# logistics/views/transport_assignment_views.py

from rest_framework import viewsets, permissions, status as drf_status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from logistics.models.transport_assignment import TransportAssignment
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle

from logistics.serializers.transport_assignment_serializer import (
    TransportAssignmentSerializer,
    TransportAssignmentWriteSerializer,
    TransportAssignmentStatusUpdateSerializer
)

class TransportAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TransportAssignment.objects.all().select_related("transport_request", "vehicle", "assigned_to")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return TransportAssignmentWriteSerializer
        return TransportAssignmentSerializer

    @action(detail=False, methods=["post"], url_path="assign-request/(?P<request_id>[^/.]+)")
    def assign_request(self, request, request_id=None):
        transport_request = get_object_or_404(TransportRequest, pk=request_id)

        if hasattr(transport_request, "transportassignment"):
            return Response({"detail": "Request already assigned."}, status=drf_status.HTTP_400_BAD_REQUEST)

        vehicle_id = request.data.get("vehicle")
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, provider__user=request.user)
        except Vehicle.DoesNotExist:
            return Response({"detail": "Invalid or unauthorized vehicle."}, status=drf_status.HTTP_400_BAD_REQUEST)

        assigned_to = request.user.transport_providers.first()
        if not assigned_to:
            return Response({"detail": "User is not a registered transport provider."}, status=drf_status.HTTP_400_BAD_REQUEST)

        assignment = TransportAssignment.objects.create(
            transport_request=transport_request,
            assigned_to=assigned_to,
            vehicle=vehicle
        )
        serializer = self.get_serializer(assignment)
        return Response(serializer.data, status=drf_status.HTTP_201_CREATED)

    def _update_status_action(self, request, assignment, new_status):
        serializer = TransportAssignmentStatusUpdateSerializer(
            instance=assignment,
            data={"assignment_status": new_status},
            context={"assignment": assignment}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": new_status}, status=drf_status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-in-transit')
    def mark_in_transit(self, request, pk=None):
        assignment = self.get_object()
        return self._update_status_action(request, assignment, TransportAssignment.STATUS_IN_TRANSIT)

    @action(detail=True, methods=['post'], url_path='mark-completed')
    def mark_completed(self, request, pk=None):
        assignment = self.get_object()
        return self._update_status_action(request, assignment, TransportAssignment.STATUS_COMPLETED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        assignment = self.get_object()
        return self._update_status_action(request, assignment, TransportAssignment.STATUS_CANCELLED)