# security/views/otp_views.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired
from security.utils.otp_helpers import (
    mask_phone, mask_email, can_request_otp, is_in_cooldown, set_otp_cooldown,
    make_otp_token, parse_otp_token
)

logger = logging.getLogger(__name__)

class RequestOTPView(APIView):
    """
    POST /api/v1/security/otp/request/
    Payload: { "email": "<email>" }  OR authenticated user
    Response: { "detail": "...", "via": "SMS|EMAIL|TOTP", "masked": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        user = None

        if request.user and getattr(request.user, "is_authenticated", False):
            user = request.user
        elif email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"detail": "Invalid user/email."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Email or authentication required."}, status=status.HTTP_400_BAD_REQUEST)

        identity = f"user:{user.id}"
        if not can_request_otp(identity):
            return Response({"detail": "Too many OTP requests. Try later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if is_in_cooldown(identity):
            return Response({"detail": "Please wait before requesting another OTP."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # If user's preferred method is TOTP (authenticator app), we just return provisioning info
        if getattr(user, "preferred_otp_method", "SMS") == "TOTP":
            # for TOTP we don't send code; client should use their authenticator app
            provisioning_uri = None
            try:
                provisioning_uri = user.get_2fa_secret()  # get_2fa_secret returns secret; generate URI on client if needed
            except Exception:
                provisioning_uri = None
            set_otp_cooldown(identity)
            return Response({
                "detail": "Use your authenticator app to generate a code.",
                "via": "TOTP",
                "provisioning": provisioning_uri
            }, status=status.HTTP_200_OK)

        # For SMS/Email: generate and send
        code = user.generate_otp()
        set_otp_cooldown(identity)

        masked = mask_phone(user.phone_number) if user.preferred_otp_method == "SMS" else mask_email(user.email)
        return Response({
            "detail": "OTP sent.",
            "via": user.preferred_otp_method,
            "masked": masked
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    POST /api/v1/security/otp/verify/
    Payload: { "email": "<email>", "code": "123456" } OR authenticated user + code
    Response: { "detail":"verified", "otp_token": "<token>" }  OR issues JWT tokens if used after login flow.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        if not code:
            return Response({"detail": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        if request.user and getattr(request.user, "is_authenticated", False):
            user = request.user
        elif email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"detail": "Invalid user/email."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Email or authentication required."}, status=status.HTTP_400_BAD_REQUEST)

        # If TOTP preferred -> verify via verify_2fa_token
        if getattr(user, "preferred_otp_method", "SMS") == "TOTP":
            if not user.verify_2fa_token(code):
                return Response({"detail": "Invalid TOTP code."}, status=status.HTTP_401_UNAUTHORIZED)
            # success -> return otp_token
            token = make_otp_token(user.id)
            return Response({"detail": "2FA/TOTP verified.", "otp_token": token}, status=status.HTTP_200_OK)

        # Else: SMS/Email OTP verify
        if not user.verify_otp(code):
            # return unauthorized
            return Response({"detail": "Invalid OTP code."}, status=status.HTTP_401_UNAUTHORIZED)

        # success: create signed otp token for API clients
        token = make_otp_token(user.id)
        # Optionally set session flag if using session-based flows
        if request.session is not None:
            request.session["otp_verified"] = {"ts": int(__import__("time").time()), "user_id": user.id}
            request.session.modified = True

        return Response({"detail": "OTP verified.", "otp_token": token}, status=status.HTTP_200_OK)
