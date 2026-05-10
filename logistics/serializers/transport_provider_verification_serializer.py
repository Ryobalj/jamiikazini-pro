# logistics/serializers/transport_provider_verification_serializer.py

from rest_framework import serializers
from logistics.models.transport_provider_verification import TransportProviderVerification
from gov_integration.serializers.service_type import VerificationRequestSerializer

class TransportProviderVerificationSerializer(serializers.ModelSerializer):
    nida_verification = VerificationRequestSerializer(read_only=True)
    driving_license_verification = VerificationRequestSerializer(read_only=True)
    vehicle_license_verification = VerificationRequestSerializer(read_only=True)
    latra_permit_verification = VerificationRequestSerializer(read_only=True)

    class Meta:
        model = TransportProviderVerification
        fields = [
            'id',
            'user',
            'institution',
            'nida_verification',
            'driving_license_verification',
            'vehicle_license_verification',
            'latra_permit_verification',
            'overall_status',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['overall_status', 'created_at', 'updated_at']