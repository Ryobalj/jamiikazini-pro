# gov_integration/views/transport_verification_views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from gov_integration.helpers.verification import (
    verify_entity,
    business_license_authority_for,
    national_id_authority_for,
    driver_license_authority_for,
    transport_license_authority_for,
)
from gov_integration.serializers.transport_verification_serializers import (
    NIDAVerificationSerializer,
    DriverLicenseVerificationSerializer,
    BusinessLicenseVerificationSerializer,
    LatraLicenseVerificationSerializer
)


class NIDAVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = NIDAVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        country_code = serializer.validated_data.get('country_code') or 'tz'
        result = verify_entity(
            country_code=country_code,
            authority_code=national_id_authority_for(country_code),
            payload={"national_id_number": serializer.validated_data['national_id_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)


class DriverLicenseVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DriverLicenseVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        country_code = serializer.validated_data.get('country_code') or 'tz'
        result = verify_entity(
            country_code=country_code,
            authority_code=driver_license_authority_for(country_code),
            payload={"license_number": serializer.validated_data['license_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)


class BusinessLicenseVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BusinessLicenseVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        country_code = serializer.validated_data.get('country_code') or 'tz'
        result = verify_entity(
            country_code=country_code,
            authority_code=business_license_authority_for(country_code),
            payload={"business_license_number": serializer.validated_data['business_license_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)


class LatraLicenseVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LatraLicenseVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        country_code = serializer.validated_data.get('country_code') or 'tz'
        result = verify_entity(
            country_code=country_code,
            authority_code=transport_license_authority_for(country_code),
            payload={"latra_license_number": serializer.validated_data['latra_license_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)
