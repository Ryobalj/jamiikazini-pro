# security/views/phone_verification_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from security.utils.otp_helpers import mask_phone, can_request_otp, is_in_cooldown, set_otp_cooldown


class RequestPhoneVerificationView(APIView):
    """
    POST /api/v1/security/phone/request/
    Authenticated only. Sends an SMS OTP to the user's OWN phone_number,
    always via SMS regardless of preferred_otp_method (proving ownership of
    this exact number, not the user's general 2FA channel).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.phone_number:
            return Response({"detail": "Hakuna namba ya simu kwenye akaunti yako."}, status=status.HTTP_400_BAD_REQUEST)
        if user.is_phone_verified:
            return Response({"detail": "Namba yako ya simu tayari imethibitishwa."}, status=status.HTTP_400_BAD_REQUEST)

        identity = f"phone_verify:{user.id}"
        if not can_request_otp(identity):
            return Response({"detail": "Umeomba OTP mara nyingi mno. Jaribu baadaye."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if is_in_cooldown(identity):
            return Response({"detail": "Subiri kidogo kabla ya kuomba OTP nyingine."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user.generate_otp(method="SMS")
        set_otp_cooldown(identity)

        return Response({"detail": "OTP imetumwa.", "masked": mask_phone(user.phone_number)}, status=status.HTTP_200_OK)


class VerifyPhoneVerificationView(APIView):
    """
    POST /api/v1/security/phone/verify/
    Payload: { "code": "123456" }
    On success, permanently sets is_phone_verified=True.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"detail": "Msimbo unahitajika."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.verify_otp(code):
            return Response({"detail": "Msimbo si sahihi au umeisha muda."}, status=status.HTTP_401_UNAUTHORIZED)

        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

        return Response({"detail": "Namba ya simu imethibitishwa.", "is_phone_verified": True}, status=status.HTTP_200_OK)
