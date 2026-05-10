import pytest
from accounts.serializers import LoginSerializer
from accounts.models import User

@pytest.mark.django_db
class TestLoginSerializer:

    def test_valid_login(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="securepassword",
            full_name="User Example",
            role="CLIENT"
        )

        data = {
            "email": "user@example.com",
            "password": "securepassword"
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["user"] == user

    def test_invalid_email(self):
        data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or "__all__" in serializer.errors
        # Depending on DRF version, error key can differ

    def test_invalid_password(self):
        user = User.objects.create_user(
            email="user2@example.com",
            password="correctpassword",
            full_name="User Two",
            role="CLIENT"
        )
        data = {
            "email": "user2@example.com",
            "password": "wrongpassword"
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or "__all__" in serializer.errors

    def test_inactive_user(self):
        user = User.objects.create_user(
            email="user3@example.com",
            password="pass1234",
            full_name="Inactive User",
            role="CLIENT",
            is_active=False
        )
        data = {
            "email": "user3@example.com",
            "password": "pass1234"
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or "__all__" in serializer.errors