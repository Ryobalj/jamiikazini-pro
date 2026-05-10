# gov_integration/serializers/verification_serializers.py

import logging
import requests
from django.conf import settings
from rest_framework import serializers
from gov_integration.models.verification_request import VerificationRequest
from kiini.models.institution import Institution
from accounts.models import User
from security.helpers.encryption import encrypt_data
from gov_integration.models.service_type import ServiceType
from gov_integration.models.country_config import CountryConfig

logger = logging.getLogger(__name__)


class EntityVerificationSerializer(serializers.Serializer):
    country_code = serializers.ChoiceField(
        choices=[
            ("tz", "Tanzania"),
            ("ke", "Kenya"),
            ("ug", "Uganda"),
            ("rw", "Rwanda"),
            ("bi", "Burundi"),
            ("ss", "South Sudan"),
        ],
        help_text="Two-letter lowercase country code"
    )
    authority_code = serializers.CharField(
        help_text="Code ya mamlaka (e.g., nida, brs, knec)"
    )
    payload = serializers.DictField(
        help_text="Data inayotakiwa na mamlaka husika"
    )

    def validate_authority_code(self, value):
        if not value.isidentifier():
            raise serializers.ValidationError("Authority code must be a valid identifier (no spaces, symbols).")
        return value.lower()


class NationalIDVerificationSerializer(serializers.Serializer):
    country = serializers.ChoiceField(choices=[
        ('TZ', 'Tanzania'),
        ('KE', 'Kenya'),
        ('UG', 'Uganda'),
        ('RW', 'Rwanda')
    ])
    national_id = serializers.CharField()

    def validate_national_id(self, value):
        country = self.initial_data.get('country')

        if country == "TZ":
            if not value.isdigit() or len(value) != 20:
                raise serializers.ValidationError("Tanzanian NIDA must be 20 digits.")

        elif country == "KE":
            if not value.isdigit() or len(value) not in [8, 9]:
                raise serializers.ValidationError("Kenyan ID must be 8 or 9 digits.")

        elif country == "UG":
            if not (value[:2].isalpha() and value[2:].isdigit() and len(value) == 13):
                raise serializers.ValidationError("Ugandan NIN must start with 2 letters followed by 11 digits.")

        elif country == "RW":
            if not value.isdigit() or len(value) != 16:
                raise serializers.ValidationError("Rwandan ID must be 16 digits.")

        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if user.is_verified:
            raise serializers.ValidationError("User is already verified.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        country = validated_data['country']
        national_id = validated_data['national_id']
        encrypted_id = encrypt_data(national_id)

        # Get or create institution
        if not user.institution:
            institution, _ = Institution.objects.get_or_create(name="Jamiikazini User")
            user.institution = institution

        # Get or create country config
        country_config, _ = CountryConfig.objects.get_or_create(code=country)

        # Default to 'FREELANCER' service
        service, _ = ServiceType.objects.get_or_create(
            code="FREELANCER",
            defaults={
                "name": "Freelancer Service",
                "country": country_config,
                "description": "Huduma kwa watu binafsi wanaojitegemea.",
                "is_active": True
            }
        )

        # Run verification
        response_data = self.perform_verification(country, national_id)
        status = "VERIFIED" if response_data.get("verified") else "FAILED"

        # Save verification attempt
        VerificationRequest.objects.create(
            user=user,
            institution=user.institution,
            country=country,
            service=service,
            payload={"national_id": encrypted_id},
            status=status,
            response_data=response_data
        )

        if status == "VERIFIED":
            user.national_id = national_id  # auto-encrypted by model
            user.is_verified = True
            user.save()
            return {"message": "User successfully verified."}

        raise serializers.ValidationError("National ID could not be verified.")

    def perform_verification(self, country, national_id):
        env = getattr(settings, "DJANGO_ENV", "development").lower()

        def simulate(success=True):
            logger.warning(f"Simulated verification for {country}")
            return {"verified": success}

        try:
            if country == "TZ":
                if env == "production" and settings.TZ_NIDA_API_KEY:
                    return self.call_api(settings.TZ_NIDA_API_URL, settings.TZ_NIDA_API_KEY, {"national_id": national_id})
                return simulate(success=national_id.isdigit() and len(national_id) == 20)

            elif country == "KE":
                if env == "production" and settings.KE_NRB_API_KEY:
                    return self.call_api(settings.KE_NRB_API_URL, settings.KE_NRB_API_KEY, {"national_id": national_id})
                return simulate(success=national_id.isdigit() and len(national_id) in [8, 9])

            elif country == "UG":
                if env == "production" and settings.UG_NIRA_API_KEY:
                    return self.call_api(settings.UG_NIRA_API_URL, settings.UG_NIRA_API_KEY, {"nin": national_id})
                return simulate(success=national_id[:2].isalpha() and national_id[2:].isdigit() and len(national_id) == 13)

            elif country == "RW":
                if env == "production" and settings.RW_NIDA_API_KEY:
                    return self.call_api(settings.RW_NIDA_API_URL, settings.RW_NIDA_API_KEY, {"national_id": national_id})
                return simulate(success=national_id.isdigit() and len(national_id) == 16)

            raise ValueError("Unsupported country.")

        except Exception as e:
            logger.error(f"Verification failed for {country}: {e}")
            return {"verified": False, "error": str(e)}

    def call_api(self, url, api_key, payload):
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()