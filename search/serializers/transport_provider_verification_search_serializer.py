# search/serializers/transport_provider_verification_search_serializer.py

from rest_framework import serializers


class VerificationRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    verified_at = serializers.DateField(allow_null=True)

    class Meta:
        # ref_name ya kipekee - inagongana na gov_integration.VerificationRequestSerializer
        ref_name = "TPVSearchVerificationRequest"


class TransportProviderVerificationSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    overall_status = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    user = serializers.DictField()
    institution = serializers.DictField()

    nida_verification = VerificationRequestSerializer()
    driving_license_verification = VerificationRequestSerializer()
    vehicle_license_verification = VerificationRequestSerializer()
    latra_permit_verification = VerificationRequestSerializer()