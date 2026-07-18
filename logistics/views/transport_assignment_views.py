# logistics/views/transport_assignment_views.py

from django.db import transaction as db_transaction
from rest_framework import viewsets, permissions, serializers, status as drf_status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from logistics.models.transport_assignment import TransportAssignment
from logistics.models.transport_request import TransportRequest
from logistics.choices import TransportRequestStatus
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle

from logistics.serializers.transport_assignment_serializer import (
    TransportAssignmentSerializer,
    TransportAssignmentWriteSerializer,
    TransportAssignmentStatusUpdateSerializer
)
from logistics.serializers.geo_fields import PointJSONField


class UpdateLocationSerializer(serializers.Serializer):
    current_location = PointJSONField()

class TransportAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TransportAssignment.objects.all().select_related("transport_request", "vehicle", "assigned_to")
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return self.queryset
        return self.queryset.filter(
            Q(assigned_to__user=user)
            | Q(transport_request__order__client=user)
            | Q(transport_request__requested_by=user)
        )

    def get_serializer_class(self):
        if self.action == "create":
            return TransportAssignmentWriteSerializer
        return TransportAssignmentSerializer

    @action(detail=False, methods=["post"], url_path="assign-request/(?P<request_id>[^/.]+)")
    @db_transaction.atomic
    def assign_request(self, request, request_id=None):
        try:
            transport_request = TransportRequest.objects.select_for_update().get(pk=request_id)
        except TransportRequest.DoesNotExist:
            return Response({"detail": "Transport request not found."}, status=drf_status.HTTP_404_NOT_FOUND)

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

        verification = getattr(request.user, "transport_verification", None)
        if not verification or verification.overall_status != "VERIFIED":
            return Response(
                {"detail": "Lazima ukamilishe uthibitisho wako (NIDA, leseni, LATRA) kabla ya kupokea kazi."},
                status=drf_status.HTTP_403_FORBIDDEN,
            )

        assignment = TransportAssignment.objects.create(
            transport_request=transport_request,
            assigned_to=assigned_to,
            vehicle=vehicle,
            agreed_fare=transport_request.estimated_fare,
        )
        transport_request.status = TransportRequestStatus.ACCEPTED
        transport_request.is_accepted = True
        transport_request.save(update_fields=["status", "is_accepted"])

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

    @action(detail=True, methods=['post'], url_path='mark-delivered')
    def mark_delivered(self, request, pk=None):
        assignment = self.get_object()
        return self._update_status_action(request, assignment, TransportAssignment.STATUS_DELIVERED)

    @action(detail=True, methods=['post'], url_path='confirm-receipt')
    def confirm_receipt(self, request, pk=None):
        assignment = self.get_object()
        tr = assignment.transport_request
        is_owner = (
            (tr.order is not None and tr.order.client_id == request.user.id)
            or tr.requested_by_id == request.user.id
        )
        if not is_owner:
            return Response({"detail": "Huwezi kuthibitisha order isiyo yako."}, status=drf_status.HTTP_403_FORBIDDEN)
        try:
            assignment.confirm_receipt()
        except ValueError as e:
            return Response({"detail": str(e)}, status=drf_status.HTTP_400_BAD_REQUEST)
        return Response({"status": "confirmed"}, status=drf_status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='update-location')
    def update_location(self, request, pk=None):
        assignment = self.get_object()
        if assignment.assigned_to.user_id != request.user.id:
            return Response(
                {"detail": "Huwezi kusasisha eneo la usafirishaji huu."},
                status=drf_status.HTTP_403_FORBIDDEN,
            )
        if assignment.assignment_status != TransportAssignment.STATUS_IN_TRANSIT:
            return Response(
                {"detail": "Unaweza kusasisha eneo wakati safari ikiendelea (IN_TRANSIT) tu."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )
        serializer = UpdateLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment.current_location = serializer.validated_data["current_location"]
        assignment.save(update_fields=["current_location"])
        return Response({"status": "updated"}, status=drf_status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-completed')
    def mark_completed(self, request, pk=None):
        assignment = self.get_object()
        return self._update_status_action(request, assignment, TransportAssignment.STATUS_COMPLETED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        assignment = self.get_object()
        return self._update_status_action(request, assignment, TransportAssignment.STATUS_CANCELLED)