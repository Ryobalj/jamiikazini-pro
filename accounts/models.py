# accounts/models.py

import secrets
import random
import pyotp
import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
)
from security.helpers.encryption import encrypt_data, decrypt_data
from django.utils import timezone


# ----------------- User Manager ----------------- #
class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_user(self, email=None, password=None, full_name='', role='', **extra_fields):
        """
        Custom create_user supporting both (email, password, full_name) and
        legacy (username, email, password) calls.
        """
        if email and "@" not in str(email):
            # Legacy: email argument ilikuwa username
            full_name = email
            email = extra_fields.get("email")
            if not email:
                raise ValueError("Email is required")

        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        # Map legacy username → full_name
        if "username" in extra_fields and not full_name:
            full_name = extra_fields.pop("username")

        user = self.model(email=email, full_name=full_name, role=role, **extra_fields)

        user.set_password(password)

        # Encrypted fields
        if "phone_number" in extra_fields:
            user.phone_number = extra_fields.pop("phone_number")
        if "device_token" in extra_fields:
            user.device_token = extra_fields.pop("device_token")
        if "national_id" in extra_fields:
            user.national_id = extra_fields.pop("national_id")

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, full_name='', role='ADMIN', **extra_fields):
        user = self.create_user(email, password, full_name, role, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ----------------- User Model ----------------- #
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('CLIENT', 'Client'),
        ('PROVIDER', 'Provider'),
        ('TRANSPORTER', 'Transporter'),
        ('INSTITUTION_ADMIN', 'Institution Admin'),
        ('ADMIN', 'Admin'),
    )

    OTP_METHOD_CHOICES = (
        ("SMS", "SMS"),
        ("EMAIL", "Email"),
        ("TOTP", "Authenticator App"),
    )

    # Institution bado ipo kama FK lakini bila default helper
    institution = models.ForeignKey(
        "kiini.Institution",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Institution anayoitambulisha user, inaweza kuwa None."
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Encrypted fields
    _phone_number = models.CharField(max_length=255, blank=True, null=True)
    _device_token = models.CharField(max_length=255, blank=True, null=True)
    _2fa_secret = models.CharField(max_length=255, blank=True, null=True)
    _national_id = models.CharField(max_length=255, blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_2fa_enabled = models.BooleanField(default=False)

    preferred_otp_method = models.CharField(
        max_length=10,
        choices=OTP_METHOD_CHOICES,
        default="SMS",
    )
    _otp_code = models.CharField(max_length=255, blank=True, null=True)
    _otp_expires_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role', 'full_name']

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    # ----------------- Encrypted Fields ----------------- #
    @property
    def phone_number(self):
        return decrypt_data(self._phone_number) if self._phone_number else None

    @phone_number.setter
    def phone_number(self, value):
        self._phone_number = encrypt_data(value)

    @property
    def device_token(self):
        return decrypt_data(self._device_token) if self._device_token else None

    @device_token.setter
    def device_token(self, value):
        self._device_token = encrypt_data(value)

    @property
    def national_id(self):
        return decrypt_data(self._national_id) if self._national_id else None

    @national_id.setter
    def national_id(self, value):
        self._national_id = encrypt_data(value)

    # ----------------- 2FA (TOTP) ----------------- #
    def get_2fa_secret(self):
        if not self._2fa_secret:
            plain = pyotp.random_base32()
            self._2fa_secret = encrypt_data(plain)
            self.save(update_fields=["_2fa_secret"])
        return decrypt_data(self._2fa_secret)

    def verify_2fa_token(self, token: str) -> bool:
        totp = pyotp.TOTP(self.get_2fa_secret())
        return totp.verify(token)

    def reset_2fa(self):
        """Reset 2FA secret and disable 2FA."""
        self._2fa_secret = None
        self.is_2fa_enabled = False
        self.save(update_fields=["_2fa_secret", "is_2fa_enabled"])

    # ----------------- OTP via SMS/Email ----------------- #
    def generate_otp(self):
        from jamiitasks.tasks.notifications import send_sms_task, send_email_task

        """Generate OTP and send via SMS/Email/TOTP"""
        # futa OTP ya zamani
        self._otp_code = None
        self._otp_expires_at = None

        code = f"{random.randint(0, 999999):06d}"  # always 6 digits
        self._otp_code = encrypt_data(code)
        self._otp_expires_at = timezone.now() + timezone.timedelta(minutes=5)
        self.save(update_fields=["_otp_code", "_otp_expires_at"])

        try:
            if self.preferred_otp_method == "SMS" and self.phone_number:
                send_sms_task.delay(self.phone_number, f"Your Jamiikazini OTP is {code}")

            elif self.preferred_otp_method == "EMAIL" and self.email:
                send_email_task.delay(
                    self.email,
                    "Your Jamiikazini OTP",
                    f"Your OTP code is {code}. It expires in 5 minutes."
                )
            # If TOTP: user uses authenticator app, no need to send
        except Exception as e:
            # log tu error bila kuzuia user kutumia OTP
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send OTP: {e}")

        return code

    def verify_otp(self, code: str) -> bool:
        """Verify OTP code (SMS/Email based)"""
        if not self._otp_code or not self._otp_expires_at:
            return False
        if timezone.now() > self._otp_expires_at:
            return False

        stored = decrypt_data(self._otp_code)
        return secrets.compare_digest(stored, str(code))

    # ----------------- Helpers ----------------- #
    @property
    def roles(self):
        return [self.role] if self.role else []

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email

    @property
    def username(self):
        """Alias kwa backward compatibility – username == full_name"""
        return self.full_name

    @property
    def first_name(self):
        """Alias kwa backward compatibility – first_name == full_name"""
        return self.full_name

    @property
    def last_name(self):
        """Alias kwa backward compatibility – last_name == full_name"""
        return self.full_name

# ----------------- Login History ----------------- #
class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Login Histories"
        ordering = ['-login_time']

    def __str__(self):
        return f"Login by {self.user.email if self.user else 'Unknown'} from {self.ip_address}"
