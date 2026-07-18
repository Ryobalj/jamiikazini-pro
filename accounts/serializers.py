# accounts/serializers.py

import re
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from accounts.models import User, LoginHistory
import requests
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()


# ========================================
# Custom FlexibleIDField
# ========================================
class FlexibleIDField(serializers.Field):
    """
    Field inayorudisha string representation kwa JSON.
    Wakati input inakuja, inajaribu convert kwa int.
    """
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        try:
            return int(data)
        except (ValueError, TypeError):
            return data

# ========================================
# User Serializers
# ========================================
class SimpleUserSerializer(serializers.ModelSerializer):
    id = FlexibleIDField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']
        read_only_fields = fields

class UserSerializer(SimpleUserSerializer):
    """Wrapper kwa backward compatibility"""
    pass

class AdminUserSerializer(serializers.ModelSerializer):
    id = FlexibleIDField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'phone_number', 'is_verified', 'is_active']

class MeSerializer(serializers.ModelSerializer):
    id = FlexibleIDField(read_only=True)
    roles = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    device_token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role',
            'phone_number', 'device_token', 'is_verified', 'is_identity_verified',
            'is_2fa_enabled', 'preferred_otp_method',
            'roles', 'institution', 'domain',
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return [obj.role] if obj.role else []

    def get_institution(self, obj):
        if hasattr(obj, 'institution') and obj.institution:
            return {
                'id': str(obj.institution.id),
                'name': obj.institution.name,
                'domain': obj.institution.domain,
            }
        return None

    def get_domain(self, obj):
        if hasattr(obj, 'institution') and obj.institution:
            return obj.institution.domain
        return None

    def get_phone_number(self, obj):
        return obj.phone_number

    def get_device_token(self, obj):
        return obj.device_token

class UserMinimalSerializer(serializers.ModelSerializer):
    id = FlexibleIDField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']

# ========================================
# Account Operations Serializers
# ========================================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    # Lazima kama email - namba ya simu inaanzishwa saa hii, uthibitisho wake
    # (OTP ya SMS) hufanyika baadaye kupitia Settings/security phone views.
    phone_number = serializers.CharField(required=True, allow_blank=False)
    recaptcha_token = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'confirm_password', 'phone_number', 'recaptcha_token']

    def validate_recaptcha_token(self, value):
        secret_key = settings.RECAPTCHA_PRIVATE_KEY
        data = {'secret': secret_key, 'response': value}
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()
        if not result.get('success'):
            raise serializers.ValidationError("Invalid reCAPTCHA. Tafadhali jaribu tena.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Barua pepe hii tayari imesajiliwa.")
        return value

    def validate(self, data):
        pw = data.get("password")
        confirm = data.get("confirm_password")
        if pw != confirm:
            raise serializers.ValidationError({"confirm_password": "Nenosiri halifanani."})

        # Password complexity checks
        if len(pw) < 8:
            raise serializers.ValidationError({"password": "Nenosiri lazima liwe na urefu wa angalau herufi 8."})
        if not re.search(r"[A-Z]", pw):
            raise serializers.ValidationError({"password": "Lazima kuwe na herufi kubwa (A-Z)."})
        if not re.search(r"[a-z]", pw):
            raise serializers.ValidationError({"password": "Lazima kuwe na herufi ndogo (a-z)."})
        if not re.search(r"\d", pw):
            raise serializers.ValidationError({"password": "Lazima kuwe na tarakimu (0-9)."})
        if not re.search(r"[!@#$%^&*()_+{}:;<>,.?~\\/-]", pw):
            raise serializers.ValidationError({"password": "Lazima kuwe na alama maalum (mfano !@#%)."})

        return data

    def validate_phone_number(self, value):
        if value and len(value) < 6:
            raise serializers.ValidationError("Nambari ya simu ni fupi sana.")
        return value

    def create(self, validated_data):
        validated_data.pop('recaptcha_token')
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        phone_number = validated_data.pop('phone_number', None)
        validated_data['role'] = 'CLIENT'
        user = User(**validated_data)
        user.set_password(password)
        if phone_number:
            user.phone_number = phone_number
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email au nenosiri si sahihi.")

        if not user.check_password(password):
            raise serializers.ValidationError("Email au nenosiri si sahihi.")

        if not user.is_active:
            raise serializers.ValidationError("Akaunti hii imezimwa.")

        data["user"] = user
        return data

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Nenosiri la zamani si sahihi.")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Nenosiri jipya ni fupi mno (angalau herufi 8).")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("Lazima kuwe na herufi kubwa (A-Z).")
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("Lazima kuwe na herufi ndogo (a-z).")
        if not re.search(r"\d", value):
            raise serializers.ValidationError("Lazima kuwe na tarakimu (0-9).")
        if not re.search(r"[!@#$%^&*()_+{}:;<>,.?~\\/-]", value):
            raise serializers.ValidationError("Lazima kuwe na alama maalum.")
        return value

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'full_name', 'role', 'phone_number', 'is_verified']
        read_only_fields = fields

class UserUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'email', 'role']
        extra_kwargs = {
            'email': {'read_only': True},
            'role': {'read_only': True},
        }

    def update(self, instance, validated_data):
        validated_data.pop('role', None)
        phone = validated_data.pop('phone_number', None)
        if phone is not None:
            instance.phone_number = phone
        return super().update(instance, validated_data)

class LoginHistorySerializer(serializers.ModelSerializer):
    # source='user.id' - vinginevyo FlexibleIDField ingerudisha str(user_object)
    # ("Jina (ROLE)") badala ya kitambulisho cha mtumiaji
    user = FlexibleIDField(source="user.id", read_only=True)

    class Meta:
        model = LoginHistory
        fields = ['user', 'login_time', 'ip_address', 'user_agent', 'was_successful']

class UserProfileSerializer(serializers.ModelSerializer):
    id = FlexibleIDField(read_only=True)
    phone_number = serializers.SerializerMethodField()
    device_token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role',
            'phone_number', 'device_token', 'is_verified',
            'is_2fa_enabled', 'created_at',
        ]

    def get_phone_number(self, obj):
        return obj.phone_number

    def get_device_token(self, obj):
        return obj.device_token

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    otp_code = serializers.CharField(required=False)  # for 2FA OTP/TOTP

    def validate(self, data):
        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid user.")
        
        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError("Invalid or expired token.")

        data['user'] = user
        return data
