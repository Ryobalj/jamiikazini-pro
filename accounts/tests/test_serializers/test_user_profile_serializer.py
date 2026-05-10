import pytest
from accounts.models import User
from accounts.serializers import UserProfileSerializer

@pytest.mark.django_db
def test_user_profile_serializer_with_encrypted_fields():
    # Create user with encrypted fields via setters
    user = User.objects.create_user(
        email="testuser@example.com",
        password="securepass123",
        full_name="Test User",
        role="CLIENT"
    )
    user.phone_number = "0755555555"
    user.device_token = "abc123xyz"
    user.is_verified = True
    user.is_2fa_enabled = True
    user.save()

    serializer = UserProfileSerializer(user)
    data = serializer.data

    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "CLIENT"
    assert data["phone_number"] == "0755555555"
    assert data["device_token"] == "abc123xyz"
    assert data["is_verified"] is True
    assert data["is_2fa_enabled"] is True
    assert "created_at" in data
    assert "id" in data
