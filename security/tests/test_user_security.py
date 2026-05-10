# security/tests/test_user_security.py

import pytest
from unittest.mock import patch
from django.utils import timezone
from accounts.models import User

@pytest.mark.django_db
class TestUserSecurity:

    @pytest.fixture(autouse=True)
    def setup_user(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="securepass123",
            full_name="Security User",
            phone_number="+255688123456"
        )

    # ----------------- 2FA Tests ----------------- #
    def test_2fa_secret_generated_once(self):
        secret1 = self.user.get_2fa_secret()
        secret2 = self.user.get_2fa_secret()
        assert secret1 == secret2
        assert secret1 is not None

    def test_2fa_verification_correct(self):
        secret = self.user.get_2fa_secret()
        import pyotp
        totp = pyotp.TOTP(secret)
        token = totp.now()
        assert self.user.verify_2fa_token(token) is True

    def test_2fa_verification_wrong(self):
        assert self.user.verify_2fa_token("000000") is False

    def test_reset_2fa_clears_secret_and_disables(self):
        self.user.get_2fa_secret()
        self.user.is_2fa_enabled = True
        self.user.save()
        self.user.reset_2fa()
        assert self.user._2fa_secret is None
        assert self.user.is_2fa_enabled is False

    # ----------------- OTP Tests ----------------- #
    @patch("jamiitasks.tasks.notifications.send_sms_task.delay")
    @patch("jamiitasks.tasks.notifications.send_email_task.delay")
    def test_generate_otp_sms_email(self, mock_email, mock_sms):
        # Test SMS delivery
        self.user.preferred_otp_method = "SMS"
        code_sms = self.user.generate_otp()
        assert len(code_sms) == 6
        mock_sms.assert_called_once()

        # Test Email delivery
        self.user.preferred_otp_method = "EMAIL"
        code_email = self.user.generate_otp()
        assert len(code_email) == 6
        mock_email.assert_called_once()

    def test_verify_correct_otp(self):
        code = self.user.generate_otp()
        assert self.user.verify_otp(code) is True

    def test_verify_wrong_otp(self):
        self.user.generate_otp()
        assert self.user.verify_otp("000000") is False

    def test_expired_otp(self):
        self.user.generate_otp()
        self.user._otp_expires_at = timezone.now() - timezone.timedelta(seconds=1)
        self.user.save(update_fields=["_otp_expires_at"])
        assert self.user.verify_otp("123456") is False