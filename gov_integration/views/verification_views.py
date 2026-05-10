# gov_integration/views/verification_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from gov_integration.serializers.verification_serializers import (
  EntityVerificationSerializer,
  NationalIDVerificationSerializer,
  )
from gov_integration.helpers.verification import verify_entity
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, permissions, throttling
from security.authentication.throttling import JamiiThrottle


class EntityVerificationView(APIView):
    """
    Accepts POST with country_code, authority_code, and payload.
    Returns verification result (real or mock).
    """

    def post(self, request):
        serializer = EntityVerificationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            result = verify_entity(
                country_code=data["country_code"],
                authority_code=data["authority_code"],
                payload=data["payload"],
                user=request.user if request.user.is_authenticated else None
            )
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NationalIDVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [JamiiThrottle]

    def post(self, request):
        serializer = NationalIDVerificationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      
        