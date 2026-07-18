# search/serializers/transport_provider_verification_search_serializer.py

from rest_framework import serializers


class VerificationRequestSerializer(serializers.Serializer):
    # required=False on both: when the underlying OneToOne verification link
    # is unset (very common - most providers haven't submitted every
    # verification type yet), django_elasticsearch_dsl's automatic ObjectField
    # resolution yields an empty object rather than None.
    id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)
    # VerificationRequest has no verified_at field - updated_at (bumped by
    # auto_now=True whenever .verify() saves) is the closest real timestamp.
    updated_at = serializers.DateField(allow_null=True, required=False)

    class Meta:
        # ref_name ya kipekee - inagongana na gov_integration.VerificationRequestSerializer
        ref_name = "TPVSearchVerificationRequest"


class TransportProviderVerificationSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    overall_status = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    user = serializers.DictField(required=False, allow_null=True)
    institution = serializers.DictField(required=False, allow_null=True)

    nida_verification = VerificationRequestSerializer(required=False, allow_null=True)
    driving_license_verification = VerificationRequestSerializer(required=False, allow_null=True)
    vehicle_license_verification = VerificationRequestSerializer(required=False, allow_null=True)
    latra_permit_verification = VerificationRequestSerializer(required=False, allow_null=True)