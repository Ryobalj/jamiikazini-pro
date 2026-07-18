# gov_integration/views/business_verification_views.py

from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework import status

from businesses.models.business import Business
from gov_integration.models.verification_request import VerificationRequest
from gov_integration.models.service_type import ServiceType
from gov_integration.models.country_config import CountryConfig
from gov_integration.helpers.verification import verify_entity, business_license_authority_for
from gov_integration.serializers.business_verification_serializers import (
    BusinessVerificationRequestSerializer,
    VerificationRequestSerializer,
)
from security.helpers.encryption import hash_data

DUPLICATE_LICENSE_MESSAGE = (
    "Namba hii ya leseni tayari imetumika kuthibitisha biashara nyingine. "
    "Kila leseni ya biashara inaruhusiwa kwenye akaunti moja tu."
)


def get_or_create_business_license_service(country_code):
    country, _ = CountryConfig.objects.get_or_create(
        code=country_code.upper(),
        defaults={"name": dict(CountryConfig.ISO_CODES).get(country_code.upper(), country_code.upper())}
    )
    service, _ = ServiceType.objects.get_or_create(
        code="BUSINESS_LICENSE",
        defaults={
            "name": "Business License Verification",
            "country": country,
            "description": "Uthibitisho wa leseni ya biashara kupitia mamlaka husika ya nchi.",
            "is_active": True,
        }
    )
    return service


def _get_owned_business(business_id, user):
    try:
        business = Business.objects.get(pk=business_id)
    except (Business.DoesNotExist, ValueError):
        raise NotFound("Business not found")
    if business.owner_id != user.id:
        raise PermissionDenied("Huna ruhusa ya biashara hii.")
    return business


class BusinessVerificationRequestView(APIView):
    """
    Mmiliki wa biashara anaomba uthibitisho wa leseni ya biashara yake.
    Inahifadhi VerificationRequest na, ikithibitishwa, inaweka Business.is_verified=True.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, business_id, *args, **kwargs):
        business = _get_owned_business(business_id, request.user)

        serializer = BusinessVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        country_code = serializer.validated_data.get('country_code') or 'tz'
        license_number = serializer.validated_data['business_license_number']

        # Leseni moja = biashara moja: hash ya kudumu inalinganishwa kabla ya
        # kuita mamlaka husika, ili tusipoteze muda kuthibitisha kitu
        # tutakachokataa mwishoni.
        license_hash = hash_data(license_number)
        if Business.objects.exclude(pk=business.pk).filter(license_number_hash=license_hash).exists():
            return Response({"business_license_number": [DUPLICATE_LICENSE_MESSAGE]}, status=status.HTTP_400_BAD_REQUEST)

        payload = {"business_license_number": license_number}
        authority_code = business_license_authority_for(country_code)
        result = verify_entity(country_code, authority_code, payload, user=request.user)

        status_value = 'VERIFIED' if result.get('status') in ('success', 'mock_success') else 'FAILED'

        service = get_or_create_business_license_service(country_code)
        vr = VerificationRequest.objects.create(
            user=request.user,
            institution=business.institution,
            business=business,
            country=country_code.upper(),
            service=service,
            payload=payload,
            status=status_value,
            response_data=result,
        )

        if status_value == 'VERIFIED':
            business.is_verified = True
            business.license_number_hash = license_hash
            try:
                business.save(update_fields=['is_verified', 'license_number_hash'])
            except IntegrityError:
                # Race guard: biashara nyingine imemaliza uthibitisho na
                # leseni hii kati ya ukaguzi hapo juu na save() hii.
                vr.status = 'FAILED'
                vr.save(update_fields=['status'])
                return Response({"business_license_number": [DUPLICATE_LICENSE_MESSAGE]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(VerificationRequestSerializer(vr).data, status=status.HTTP_201_CREATED)


class BusinessVerificationStatusView(APIView):
    """
    Historia/hali ya maombi ya uthibitisho ya biashara fulani (mmiliki pekee).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id, *args, **kwargs):
        business = _get_owned_business(business_id, request.user)

        requests_qs = business.verification_requests.order_by('-created_at')
        return Response({
            "is_verified": business.is_verified,
            "requests": VerificationRequestSerializer(requests_qs, many=True).data,
        })
