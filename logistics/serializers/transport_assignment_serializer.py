# logistics/serializers/transport_assignment_serializer.py

from rest_framework import serializers
from logistics.models.transport_assignment import TransportAssignment
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle
from logistics.serializers.geo_fields import PointJSONField


class TransportAssignmentSerializer(serializers.ModelSerializer):
    transport_request = serializers.PrimaryKeyRelatedField(read_only=True)
    assigned_to = serializers.StringRelatedField()
    vehicle = serializers.StringRelatedField()
    current_location = PointJSONField(read_only=True)

    class Meta:
        model = TransportAssignment
        fields = [
            "id",
            "transport_request",
            "assigned_to",
            "vehicle",
            "assignment_status",
            "pickup_time",
            "delivery_time",
            "current_location",
            "agreed_fare",
            "client_confirmed_at",
            "updated_at"
        ]


class TransportAssignmentWriteSerializer(serializers.ModelSerializer):
    current_location = PointJSONField(required=False, allow_null=True)

    class Meta:
        model = TransportAssignment
        fields = [
            "transport_request",
            "assigned_to",
            "vehicle",
            "pickup_time",
            "delivery_time",
            "current_location"
        ]

    def validate(self, data):
        request = data.get("transport_request")
        if TransportAssignment.objects.filter(transport_request=request).exists():
            raise serializers.ValidationError("Assignment already exists for this request.")
        return data


class TransportAssignmentStatusUpdateSerializer(serializers.Serializer):
    assignment_status = serializers.ChoiceField(choices=TransportAssignment.STATUS_CHOICES)

    def validate_assignment_status(self, value):
        assignment = self.context["assignment"]
        current = assignment.assignment_status
        allowed = TransportAssignment.VALID_TRANSITIONS.get(current, [])

        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot change status from {current} to {value}."
            )
        return value

    def update(self, instance, validated_data):
        new_status = validated_data["assignment_status"]
        instance.update_status(new_status)
        return instance

    def create(self, validated_data):
        raise NotImplementedError("Use this serializer with an existing instance only.")