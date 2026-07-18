# accounts/views.py

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

from django.utils.timezone import now
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail

from .models import User, LoginHistory
from accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    UserDetailSerializer,
    UserProfileSerializer,
    MeSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from helpers.request import get_client_ip
from kiini.helpers.domain import generate_subdomain_url
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)
User = get_user_model()


# ----------------- Register ----------------- #
@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save(role='CLIENT')  # Force CLIENT role
        request = self.request

        # Log registration history
        try:
            LoginHistory.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                was_successful=True
            )
        except Exception as e:
            logger.warning(f"LoginHistory logging failed: {e}")

        # Send verification email
        if not user.is_verified:
            try:
                token = default_token_generator.make_token(user)
                verification_url = generate_subdomain_url(
                    domain="auth.jamiikazini.com",
                    path=reverse("accounts:verify-email", kwargs={"user_id": user.id, "token": token})
                )
                subject = "Verify Your Email"
                message = f"Hello {user.full_name},\n\nPlease verify your email by clicking:\n{verification_url}\n\nThank you!"
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            except Exception as e:
                logger.error(f"Failed to send verification email to {user.email}: {e}")


# ----------------- Verify Email ----------------- #
@method_decorator(ensure_csrf_cookie, name='dispatch')
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id, token):
        try:
            user = User.objects.get(id=user_id)
            if default_token_generator.check_token(user, token):
                user.is_verified = True
                user.save()
                return Response({'message': 'Email verified successfully'})
        except User.DoesNotExist:
            pass
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


# ----------------- Change Password ----------------- #
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Change password for authenticated user with optional 2FA verification.
        """
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        otp_code = serializer.validated_data.get("otp_code")

        # 2FA verification
        if user.is_2fa_enabled:
            if not otp_code:
                return Response({"detail": "2FA code is required."}, status=status.HTTP_403_FORBIDDEN)

            valid_otp = False
            if user.preferred_otp_method in ["SMS", "EMAIL"]:
                valid_otp = user.verify_otp(otp_code)
            elif user.preferred_otp_method == "TOTP":
                valid_otp = user.verify_2fa_token(otp_code)

            if not valid_otp:
                return Response({"detail": "Invalid 2FA code."}, status=status.HTTP_403_FORBIDDEN)

        # Change password
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Optional: Invalidate refresh tokens
        try:
            RefreshToken.for_user(user).blacklist()
        except Exception:
            pass

        # Log the password change
        try:
            LoginHistory.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                was_successful=True
            )
        except Exception:
            pass

        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


# ----------------- Forgot Password ----------------- #
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            reset_url = generate_subdomain_url(
                domain="auth.jamiikazini.com",
                path=reverse("accounts:reset-password", kwargs={"user_id": user.id, "token": token})
            )
            subject = "Password Reset Request"
            message = f"Hello {user.full_name},\n\nReset your password by clicking:\n{reset_url}\n\nThis link expires in 1 hour."
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except User.DoesNotExist:
            pass  # Do not reveal user existence

        return Response({"detail": "If the email exists, a reset link has been sent."}, status=status.HTTP_200_OK)


# ----------------- Reset Password ----------------- #
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id, token):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(id=user_id)
            if not default_token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

            otp_code = serializer.validated_data.get("otp_code")
            if user.is_2fa_enabled:
                if not otp_code:
                    return Response({"detail": "2FA code is required."}, status=status.HTTP_403_FORBIDDEN)

                valid_otp = False
                if user.preferred_otp_method in ["SMS", "EMAIL"]:
                    valid_otp = user.verify_otp(otp_code)
                elif user.preferred_otp_method == "TOTP":
                    valid_otp = user.verify_2fa_token(otp_code)

                if not valid_otp:
                    return Response({"detail": "Invalid 2FA code."}, status=status.HTTP_403_FORBIDDEN)

            # Change password
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            # Optional: Invalidate refresh tokens
            try:
                RefreshToken.for_user(user).blacklist()
            except Exception:
                pass

            # Log the reset
            try:
                LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    was_successful=True
                )
            except Exception:
                pass

            return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


# ----------------- User Info ----------------- #
@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    # Sehemu chache tu mtumiaji anaweza kujibadilishia mwenyewe - MeSerializer
    # ina read_only_fields = fields (yote), hivyo haitumiki kwa uandishi hapa;
    # tunathibitisha moja kwa moja na kuweka field kwenye request.user.
    PATCHABLE_FIELDS = {"preferred_otp_method", "full_name"}
    VALID_OTP_METHODS = {"SMS", "EMAIL", "TOTP"}

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        data = {k: v for k, v in request.data.items() if k in self.PATCHABLE_FIELDS}
        if not data:
            return Response({"detail": "Hakuna sehemu halali ya kubadilisha."}, status=status.HTTP_400_BAD_REQUEST)

        if "preferred_otp_method" in data and data["preferred_otp_method"] not in self.VALID_OTP_METHODS:
            return Response(
                {"preferred_otp_method": "Chagua SMS, EMAIL au TOTP."}, status=status.HTTP_400_BAD_REQUEST,
            )
        if "full_name" in data and not str(data["full_name"]).strip():
            return Response({"full_name": "Jina haliwezi kuwa tupu."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        for field, value in data.items():
            setattr(user, field, value)
        user.save(update_fields=list(data.keys()))

        return Response(MeSerializer(user).data)