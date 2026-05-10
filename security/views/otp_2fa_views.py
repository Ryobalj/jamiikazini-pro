# security/views/otp_2fa_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
  AllowAny, 
  IsAuthenticated,
  )
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
import pyotp
import qrcode
import io
import base64


class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        secret = user.get_2fa_secret()
        # Generate provisioning URI for Google Authenticator app
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Jamiikazini")
        # Generate QR code image as base64
        qr = qrcode.make(uri)
        buffered = io.BytesIO()
        qr.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        return Response({"otp_uri": uri, "qr_code": qr_base64})

    def post(self, request):
        user = request.user
        token = request.data.get("token")
        if user.verify_2fa_token(token):
            user.is_2fa_enabled = True
            user.save()
            return Response({"detail": "2FA enabled successfully."})
        return Response({"detail": "Invalid token."}, status=400)


class Verify2FAView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        token = request.data.get("token")

        if not email or not token:
            return Response({"detail": "Email and token are required."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid user.")

        if not user.is_2fa_enabled or not user._2fa_secret:
            return Response({"detail": "2FA is not enabled for this user."}, status=400)

        totp = pyotp.TOTP(user._2fa_secret)
        if not totp.verify(token):
            raise AuthenticationFailed("Invalid 2FA token.")

        # On success, generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            "detail": "2FA verification successful.",
            "access": access_token,
            "refresh": refresh_token
        }, status=200)

