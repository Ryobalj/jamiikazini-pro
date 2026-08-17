# logistics/serializers/transport_provider_serializer.py

from rest_framework import serializers
from logistics.models.transport_provider import TransportProvider
from logistics.models.transport_provider_verification import TransportProviderVerification
from gov_integration.models.verification_request import VerificationRequest
from accounts.serializers import SimpleUserSerializer
from kiini.serializers.institution_serializers import InstitutionSerializer
from logistics.serializers.geo_fields import PointJSONField


class VerificationRequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = ['id', 'status', 'created_at', 'updated_at']


class TransportProviderSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)
    provider_type_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    location = PointJSONField(required=False, allow_null=True)

    class Meta:
        model = TransportProvider
        fields = [
            'id',
            'user',
            'institution',
            'provider_type',
            'provider_type_display',
            'country_code',
            'company_name',
            'company_registration_number',
            'location',
            'is_approved',
            'approval_letter',
            'profile_image',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'provider_type_display']

    def validate(self, data):
        is_approved = data.get('is_approved', False)
        approval_letter = data.get('approval_letter')

        if is_approved and not approval_letter:
            raise serializers.ValidationError({
                "approval_letter": "Unapaswa kupakia barua ya uthibitisho kabla ya kuidhinishwa."
            })

        provider_type = data.get('provider_type', getattr(self.instance, 'provider_type', None))
        company_name = data.get('company_name', getattr(self.instance, 'company_name', ''))
        if provider_type == 'company' and not company_name:
            raise serializers.ValidationError({
                "company_name": "Kampuni ya usafirishaji lazima iwe na jina."
            })
        return data

    def validate_provider_type(self, value):
        if value not in dict(TransportProvider.ProviderType.choices).keys():
            raise serializers.ValidationError("Aina ya mtoa huduma si halali.")
        return value


class TransportProviderVerificationSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)

    nida_verification = VerificationRequestStatusSerializer(read_only=True)
    driving_license_verification = VerificationRequestStatusSerializer(read_only=True)

    class Meta:
        model = TransportProviderVerification
        fields = [
            'id',
            'user',
            'institution',
            'nida_verification',
            'driving_license_verification',
            'overall_status',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'overall_status']
        # ref_name ya kipekee - inagongana na transport_provider_verification_serializer
        # yenye TransportProviderVerificationSerializer jina lile lile kwenye schema
        ref_name = "TransportProviderVerificationNested"
