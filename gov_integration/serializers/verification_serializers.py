# gov_integration/serializers/verification_serializers.py

import logging
from django.conf import settings
from django.db import IntegrityError
from rest_framework import serializers
from gov_integration.models.verification_request import VerificationRequest
from kiini.models.institution import Institution
from accounts.models import User
from security.helpers.encryption import encrypt_data, hash_data
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
        ('RW', 'Rwanda'),
        ('BI', 'Burundi'),
        ('SS', 'South Sudan'),
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

        elif country in ("BI", "SS"):
            # Format rasmi ya CNI ya Burundi / NIN ya South Sudan bado
            # hazijathibitishwa na mamlaka husika (ONI / NIA) - tunakubali
            # alphanumeric 6-20 kwa ulegevu mpaka spec rasmi ipatikane.
            if not value.isalnum() or not (6 <= len(value) <= 20):
                raise serializers.ValidationError("National ID must be 6-20 alphanumeric characters.")

        return value

    def validate(self, attrs):
        user = self.context['request'].user
        # is_verified inawekwa pia na uthibitisho wa barua pepe tu - hivyo si
        # kigezo sahihi cha kuzuia kurudia hapa. is_identity_verified ndiyo
        # inayowekwa na NIDA/national-ID pekee.
        if user.is_identity_verified:
            raise serializers.ValidationError("User is already verified.")

        # NIDA/NIN moja = akaunti moja: hash ya kudumu inalinganishwa kwa sababu
        # Fernet ciphertext haiwezi ku-queriwa kwa usawa.
        nid_hash = hash_data(attrs['national_id'])
        if User.objects.exclude(pk=user.pk).filter(national_id_hash=nid_hash).exists():
            raise serializers.ValidationError(
                {"national_id": "Kitambulisho hiki tayari kimetumika kwenye akaunti nyingine. "
                                "Kila NIDA/NIN inaruhusiwa kwenye akaunti moja tu."}
            )
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
            user.national_id = national_id  # auto-encrypted + hashed by model
            user.is_verified = True
            user.is_identity_verified = True
            try:
                user.save()
            except IntegrityError:
                # Race guard: akaunti nyingine imemaliza uthibitisho na NIN
                # hii kati ya validate() na save() - unique constraint ya
                # national_id_hash ndiyo mstari wa mwisho wa ulinzi.
                raise serializers.ValidationError(
                    {"national_id": "Kitambulisho hiki tayari kimetumika kwenye akaunti nyingine. "
                                    "Kila NIDA/NIN inaruhusiwa kwenye akaunti moja tu."}
                )
            return {"message": "User successfully verified."}

        raise serializers.ValidationError("National ID could not be verified.")

    def perform_verification(self, country, national_id):
        """
        Inatumia registry ileile ya mamlaka (gov_api_config + verify_entity)
        inayotumika na uthibitisho wa madereva/biashara/usafirishaji - env vars
        (mf. TZ_NIDA_API_URL/API_KEY) ndizo zinazowasha API halisi kwa kila
        nchi. Production ni fail-closed ndani ya verify_entity; development
        inatumia mock (format tayari imekaguliwa na validate_national_id).
        """
        from gov_integration.helpers.verification import verify_entity, national_id_authority_for

        result = verify_entity(
            country_code=country.lower(),
            authority_code=national_id_authority_for(country),
            payload={
                "national_id_number": national_id,
                "national_id": national_id,
            },
            user=self.context["request"].user,
        )

        verified = bool(result.get("verified")) or result.get("status") == "success"
        return {"verified": verified, **{k: v for k, v in result.items() if k != "verified"}}