# gov_integration/views/transport_verification_views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from gov_integration.helpers.verification import verify_entity
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

        result = verify_entity(
            country_code="tz",
            authority_code="nida",
            payload={"national_id_number": serializer.validated_data['national_id_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)


class DriverLicenseVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DriverLicenseVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = verify_entity(
            country_code="tz",
            authority_code="tra_driver",
            payload={"license_number": serializer.validated_data['license_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)


class BusinessLicenseVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BusinessLicenseVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = verify_entity(
            country_code="tz",
            authority_code="brela",
            payload={"business_license_number": serializer.validated_data['business_license_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)


class LatraLicenseVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LatraLicenseVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = verify_entity(
            country_code="tz",
            authority_code="latra",
            payload={"latra_license_number": serializer.validated_data['latra_license_number']},
            user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)