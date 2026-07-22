# logistics/serializers/fare_proposal_serializer.py

from rest_framework import serializers

from logistics.models.fare_proposal import FareProposal
from logistics.models.transport_request import TransportRequest
from logistics.models.vehicle import Vehicle
from logistics.choices import TransportRequestStatus


class FareProposalSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.user.full_name", read_only=True, default=None)
    vehicle_type = serializers.CharField(source="vehicle.vehicle_type", read_only=True)

    class Meta:
        model = FareProposal
        fields = [
            "id", "transport_request", "provider", "provider_name",
            "vehicle", "vehicle_type", "proposed_fare", "status", "created_at",
        ]
        read_only_fields = ["id", "provider", "status", "created_at"]

    def validate(self, attrs):
        transport_request = attrs["transport_request"]
        if transport_request.status != TransportRequestStatus.PENDING:
            raise serializers.ValidationError(
                "Ombi hili tayari limekubaliwa na dereva mwingine."
            )

        request = self.context["request"]
        provider = request.user.transport_providers.first()
        if not provider:
            raise serializers.ValidationError("Wewe si dereva aliyesajiliwa.")

        verification = getattr(request.user, "transport_verification", None)
        if not verification or verification.overall_status != "VERIFIED":
            raise serializers.ValidationError(
                "Lazima ukamilishe uthibitisho wako (NIDA, leseni, LATRA) kabla ya kupendekeza bei."
            )

        vehicle = attrs["vehicle"]
        if vehicle.provider_id != provider.id:
            raise serializers.ValidationError({"vehicle": "Gari hili si lako."})

        vehicle_verification = getattr(vehicle, "verification", None)
        if not vehicle_verification or vehicle_verification.overall_status != "VERIFIED":
            raise serializers.ValidationError(
                {"vehicle": "Gari hili bado halijathibitishwa (TRA/LATRA). Lithibitishe kwanza."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["provider"] = request.user.transport_providers.first()
        return super().create(validated_data)
