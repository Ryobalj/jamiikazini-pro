# businesses/serializers/booking_serializer.py

from django.utils import timezone
from rest_framework import serializers
from businesses.models.booking import Booking, BookingLog
from accounts.models import User
from businesses.models.service import Service
from accounts.serializers import SimpleUserSerializer
from businesses.serializers.service_serializer import ServiceSerializer
from django.utils.translation import gettext_lazy as _


class BookingSerializer(serializers.ModelSerializer):
    """Serializer kwa ajili ya kuunda booking mpya"""
    
    class Meta:
        model = Booking
        fields = [
            'id', 'client', 'service', 'scheduled_datetime', 'notes',
        ]
        read_only_fields = ['client']  # Client hatapokelewa kutoka kwa user

    def validate_scheduled_datetime(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(_("Muda wa booking lazima uwe baada ya sasa"))
        return value

    def create(self, validated_data):
        validated_data["client"] = self.context["request"].user  # Inject current user
        return super().create(validated_data)


class BookingDetailSerializer(serializers.ModelSerializer):
    """Serializer wa kusoma booking kwa kina"""
    client = SimpleUserSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    estimated_end_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'client', 'service', 'scheduled_datetime', 'notes',
            'status', 'payment_status', 'actual_start_time', 'actual_end_time',
            'cancellation_reason', 'payment_reference', 'estimated_end_time',
            'created_at', 'updated_at'
        ]


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    """Kubadilisha status ya booking au kukanseli"""
    class Meta:
        model = Booking
        fields = ['status', 'cancellation_reason']

    def validate(self, attrs):
        if attrs.get('status') == 'CANCELLED' and not attrs.get('cancellation_reason'):
            raise serializers.ValidationError({
                'cancellation_reason': _("Sababu ya kughairi lazima ijazwe.")
            })
        return attrs


class BookingLogSerializer(serializers.ModelSerializer):
    """Kusoma historia ya matukio ya booking"""
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = BookingLog
        fields = [
            'id', 'booking', 'user', 'actor_type', 'action',
            'ip_address', 'user_agent', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class BookingLogCreateSerializer(serializers.ModelSerializer):
    """Kuandika log mpya ya booking"""

    class Meta:
        model = BookingLog
        fields = [
            'booking', 'actor_type', 'action',
            'ip_address', 'user_agent', 'metadata',
        ]

    def validate_action(self, value):
        if not value:
            raise serializers.ValidationError(_("Matendo hayawezi kuwa tupu."))
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)