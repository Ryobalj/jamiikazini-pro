# businesses/views/booking_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from businesses.models.booking import Booking, BookingLog
from businesses.serializers.booking_serializer import (
    BookingSerializer,
    BookingDetailSerializer,
    BookingStatusUpdateSerializer,
    BookingLogSerializer,
    BookingLogCreateSerializer,
)
from businesses.permissions import IsBookingOwnerOrStaffOrReadOnly
from security.mixins.admin_2fa_mixin import Admin2FAMixin


class BookingViewSet(Admin2FAMixin, viewsets.ModelViewSet):
    """
    Booking management:
    - Clients can create bookings
    - Admin/staff actions require 2FA enforcement for create/update/destroy
    """
    queryset = Booking.objects.all().select_related('client', 'service')
    permission_classes = [IsAuthenticated, IsBookingOwnerOrStaffOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return BookingSerializer
        elif self.action == "update_status":
            return BookingStatusUpdateSerializer
        return BookingDetailSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        BookingLog.objects.create(
            booking=instance,
            user=self.request.user,
            actor_type="CLIENT",
            action="CREATED",
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
            metadata={"notes": serializer.validated_data.get("notes", "")}
        )

    def get_client_ip(self):
        x_forwarded = self.request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded.split(",")[0] if x_forwarded else self.request.META.get("REMOTE_ADDR")

    @action(detail=True, methods=["patch"], url_path="status", permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingStatusUpdateSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        BookingLog.objects.create(
            booking=booking,
            user=request.user,
            actor_type="CLIENT",
            action=f"STATUS_CHANGED_TO_{serializer.validated_data['status']}",
            ip_address=self.get_client_ip(),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"reason": serializer.validated_data.get("cancellation_reason", "")}
        )
        return Response({"detail": "Status updated"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="logs", permission_classes=[IsAuthenticated])
    def logs(self, request, pk=None):
        booking = self.get_object()
        logs = booking.logs.select_related("user").all()
        serializer = BookingLogSerializer(logs, many=True)
        return Response(serializer.data)


class BookingLogViewSet(viewsets.ModelViewSet):
    queryset = BookingLog.objects.all().select_related('booking', 'user')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookingLogCreateSerializer
        return BookingLogSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)