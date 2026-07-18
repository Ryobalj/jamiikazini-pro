# gov_integration/serializers/business_verification_serializers.py

from rest_framework import serializers
from gov_integration.models.verification_request import VerificationRequest


class BusinessVerificationRequestSerializer(serializers.Serializer):
    business_license_number = serializers.CharField()
    country_code = serializers.CharField(required=False, default="tz")


class VerificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = [
            "id", "business", "institution", "country", "status",
            "payload", "response_data", "created_at", "updated_at",
        ]
        read_only_fields = fields
