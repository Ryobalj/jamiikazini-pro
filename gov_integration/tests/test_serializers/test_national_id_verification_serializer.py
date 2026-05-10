import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from gov_integration.serializers.verification_serializers import NationalIDVerificationSerializer
from kiini.models.institution import Institution
from gov_integration.models.verification_request import VerificationRequest

User = get_user_model()


@pytest.mark.django_db
class TestNationalIDVerificationSerializer:

    def setup_method(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            full_name="Test User",
            role="CLIENT"
        )

    def test_valid_tanzanian_nida(self):
        data = {"country": "TZ", "national_id": "12345678901234567890"}
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
        result = serializer.save()
        self.user.refresh_from_db()
        assert self.user.is_verified is True
        assert self.user.national_id == "12345678901234567890"
        assert VerificationRequest.objects.filter(user=self.user, country="TZ").exists()
        assert result["message"] == "User successfully verified."

    def test_invalid_tanzanian_nida_length(self):
        data = {"country": "TZ", "national_id": "12345"}
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "Tanzanian NIDA must be 20 digits." in str(serializer.errors)

    def test_valid_kenyan_id(self):
        data = {"country": "KE", "national_id": "12345678"}
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        assert serializer.is_valid()

    def test_invalid_kenyan_id_format(self):
        data = {"country": "KE", "national_id": "1234abcd"}
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "Kenyan ID must be 8 or 9 digits." in str(serializer.errors)

    def test_valid_ugandan_nin(self):
        data = {"country": "UG", "national_id": "CM12345678901"}
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        assert serializer.is_valid()

    def test_invalid_ugandan_nin_format(self):
        data = {"country": "UG", "national_id": "12345678901"}
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()
        assert "Ugandan NIN must start with 2 letters" in str(serializer.errors)

    def test_valid_rwandan_id(self):
        data = {"country": "RW", "national_id": "1234567890123456"}
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        assert serializer.is_valid()

    def test_already_verified_user(self):
        self.user.is_verified = True
        self.user.save()
        data = {"country": "TZ", "national_id": "12345678901234567890"}  # valid TZ NIDA
        request = self.factory.post("/", data)
        request.user = self.user
        serializer = NationalIDVerificationSerializer(data=data, context={"request": request})
        
        assert not serializer.is_valid()
        assert "User is already verified." in str(serializer.errors["non_field_errors"])