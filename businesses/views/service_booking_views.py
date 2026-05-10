# businesses/views/service_booking_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from businesses.models.booking import Booking
from businesses.serializers.booking_serializer import BookingSerializer
from kiini.permissions.access import IsBusinessOwnerOrReadOnly
from security.decorators import conditional_2fa_required


class ServiceBookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsBusinessOwnerOrReadOnly()]

    def get_queryset(self):
        service_id = self.kwargs.get("service_pk")
        if not service_id:
            raise ValidationError({"detail": "Missing required service ID."})

        queryset = Booking.objects.filter(service_id=service_id).select_related(
            "client", "service", "service__business"
        )

        user = self.request.user
        if user.is_staff or user.role == "INSTITUTION_ADMIN":
            return queryset
        return queryset.filter(service__business__owner=user)

    def perform_create(self, serializer):
        service_id = self.kwargs.get("service_pk")
        if not service_id:
            raise ValidationError({"detail": "Missing service ID in URL."})

        serializer.save(
            service_id=service_id,
            client=self.request.user
        )

    @conditional_2fa_required(action_type="admin_action")
    def perform_update(self, serializer):
        serializer.save()

    @conditional_2fa_required(action_type="admin_action")
    def perform_destroy(self, instance):
        instance.delete()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context