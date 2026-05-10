import pytest
from django.utils import timezone
from accounts.models import User, LoginHistory
from security.helpers.encryption import decrypt_data

@pytest.mark.django_db
class TestUserModel:

    def test_create_user_minimal(self):
        user = User.objects.create_user(email="test@example.com", password="pass123", full_name="Test User", role="CLIENT")
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "CLIENT"
        assert user.check_password("pass123")
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(email="admin@example.com", password="adminpass")
        assert superuser.is_staff
        assert superuser.is_superuser
        assert superuser.role == "ADMIN"
        assert superuser.check_password("adminpass")

    def test_encrypted_fields(self):
        user = User.objects.create_user(email="enc@example.com", password="pass", full_name="Enc User", role="CLIENT",
                                        phone_number="+255688123456", device_token="token123", national_id="NID123")
        # Decrypt via property
        assert user.phone_number == "+255688123456"
        assert user.device_token == "token123"
        assert user.national_id == "NID123"
        # Check raw DB fields are encrypted
        assert user._phone_number != "+255688123456"
        assert user._device_token != "token123"
        assert user._national_id != "NID123"

    def test_2fa_generate_verify_reset(self):
        user = User.objects.create_user(email="2fa@example.com", password="pass", full_name="2FA User", role="CLIENT")
        secret = user.get_2fa_secret()
        assert secret is not None
        # TOTP verification works
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert user.verify_2fa_token(code)
        # Reset 2FA
        user.reset_2fa()
        assert user._2fa_secret is None
        assert not user.is_2fa_enabled

    def test_otp_generate_verify(self, mocker):
        user = User.objects.create_user(email="otp@example.com", password="pass", full_name="OTP User", role="CLIENT")
        user.phone_number = "+255688123456"
        user.email = "otp@example.com"
        user.preferred_otp_method = "SMS"

        # Patch SMS/Email tasks to avoid sending
        mocker.patch("jamiitasks.tasks.notifications.send_sms_task.delay")
        mocker.patch("jamiitasks.tasks.notifications.send_email_task.delay")

        code = user.generate_otp()
        assert len(code) == 6
        assert user._otp_code is not None
        assert user._otp_expires_at > timezone.now()

        # Correct OTP
        assert user.verify_otp(code)
        # Wrong OTP
        assert not user.verify_otp("000000")
        # Expired OTP
        user._otp_expires_at = timezone.now() - timezone.timedelta(minutes=1)
        user.save(update_fields=["_otp_expires_at"])
        assert not user.verify_otp(code)

    def test_roles_property_and_names(self):
        user = User.objects.create_user(email="role@example.com", password="pass", full_name="Role User", role="CLIENT")
        assert user.roles == ["CLIENT"]
        assert user.get_full_name() == "Role User"
        assert user.get_short_name() == "Role"
        assert user.username == "Role User"

@pytest.mark.django_db
class TestLoginHistory:

    def test_create_login_history(self, user_factory):
        user = user_factory()
        log = LoginHistory.objects.create(user=user, ip_address="127.0.0.1", user_agent="pytest", was_successful=True)
        assert log.user == user
        assert log.ip_address == "127.0.0.1"
        assert log.user_agent == "pytest"
        assert log.was_successful
        assert str(log) == f"Login by {user.email} from 127.0.0.1"