# security/views/security_auth.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone

from security.authentication.throttling import JamiiThrottle
from accounts.serializers import LoginSerializer
from security.helpers.security import BaseLoginLogger
from security.helpers.recaptcha import verify_recaptcha_v3
from accounts.models import LoginHistory
from security.helpers.login_alerts import check_failed_logins_and_alert


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UnifiedLoginView(APIView):
    """
    Unified login endpoint with:
    - ReCAPTCHA v3 (skipped in DEBUG mode)
    - JWT token issuance
    - 2FA handling
    - Failed login recording + alerts
    """
    permission_classes = [AllowAny]
    throttle_classes = [JamiiThrottle]

    def post(self, request):
        use_cookies = request.query_params.get("use_cookies") == "true"
        # user_agent column ni NOT NULL - epuka None wakati header haipo
        user_agent = request.META.get("HTTP_USER_AGENT") or ""

        # Step 0: Verify ReCAPTCHA v3 (SKIP in DEBUG/Development)
        remote_ip = request.META.get("REMOTE_ADDR")
        
        # Skip recaptcha verification in DEBUG or during tests (pytest forces DEBUG=False)
        if settings.DEBUG or getattr(settings, "TESTING", False):
            pass  # [DEV/TEST] reCAPTCHA imerukwa
        else:
            recaptcha_token = request.data.get("recaptcha_token")
            if not recaptcha_token or not verify_recaptcha_v3(
                token=recaptcha_token,
                remote_ip=remote_ip,
                expected_action="login"
            ):
                return Response(
                    {"detail": "ReCAPTCHA verification failed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # USALAMA: usifichue kama barua pepe imesajiliwa au la. Barua pepe isiyokuwepo
        # NA nenosiri baya zote hurudisha 401 "Invalid credentials" sawa (hakuna 404
        # tofauti wala "Invalid password" inayothibitisha barua pepe ipo).
        email = request.data.get("email")
        from accounts.models import User

        # Step 1: Validate credentials
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            # Record failed login kama mtumiaji yupo (bila kufichua kwa mteja)
            user_instance = User.objects.filter(email=email).first() if email else None
            if user_instance:
                LoginHistory.objects.create(
                    user=user_instance,
                    ip_address=remote_ip,
                    user_agent=user_agent,
                    was_successful=False
                )
                # Trigger alerts if threshold exceeded
                check_failed_logins_and_alert(user_instance)

            BaseLoginLogger.log_failure(request)

            # Ujumbe wa jumla - usifichue ni barua pepe au nenosiri lililokosea
            return Response(
                {"detail": "Invalid credentials.", "code": "invalid_credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = serializer.validated_data["user"]

        # Record successful login
        LoginHistory.objects.create(
            user=user,
            ip_address=remote_ip,
            user_agent=user_agent,
            was_successful=True
        )

        # Step 2: Handle 2FA
        if user.is_2fa_enabled:
            BaseLoginLogger.log_success(request, user)
            return Response({
                "2fa_required": True,
                "detail": "2FA required.",
                "email": user.email
            }, status=status.HTTP_403_FORBIDDEN)

        # Step 3: Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        BaseLoginLogger.log_success(request, user)

        response_data = {
            "detail": "Login successful.",
            "access": access_token,
            "refresh": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }
        }

        # Step 4: Set cookies if requested
        response = Response(response_data, status=status.HTTP_200_OK)
        if use_cookies:
            response.set_cookie(
                key="access",
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=15 * 60
            )
            response.set_cookie(
                key="refresh",
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60
            )

        return response


class LogoutView(APIView):
    """
    Logout endpoint: blacklists refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)