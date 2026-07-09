import pytest
from unittest.mock import patch
from accounts.serializers import RegisterSerializer
from accounts.models import User

@pytest.mark.django_db
class TestRegisterSerializer:

    @patch('accounts.serializers.requests.post')
    def test_valid_registration(self, mock_post):
        mock_post.return_value.json.return_value = {'success': True}

        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'Strongpass123!',
            'confirm_password': 'Strongpass123!',
            'recaptcha_token': 'fake-token',
            'phone_number': '0712345678',
        }

        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()
        assert user.email == data['email']
        assert user.full_name == data['full_name']
        assert user.role == 'CLIENT'
        assert user.check_password(data['password'])
        assert user.phone_number == data['phone_number']

    @patch('accounts.serializers.requests.post')
    def test_invalid_recaptcha(self, mock_post):
        mock_post.return_value.json.return_value = {'success': False}

        data = {
            'email': 'recaptcha@example.com',
            'full_name': 'ReCaptcha Fail',
            'password': 'Strongpass123!',
            'confirm_password': 'Strongpass123!',
            'recaptcha_token': 'invalid-token',
        }

        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'recaptcha_token' in serializer.errors
        assert "reCAPTCHA" in serializer.errors['recaptcha_token'][0]

    def test_email_already_exists(self):
        User.objects.create_user(
            email='existing@example.com',
            password='pass123',
            full_name='Existing User',
            role='CLIENT'
        )

        data = {
            'email': 'existing@example.com',
            'full_name': 'New User',
            'password': 'Strongpass123!',
            'confirm_password': 'Strongpass123!',
            'recaptcha_token': 'any-token',
        }

        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        # Barua pepe iliyokwisha sajiliwa - DRF UniqueValidator hutoa "already exists",
        # validate_email ya Kiswahili hutoa "tayari"; kubali chochote kinachoonyesha unique
        err = str(serializer.errors['email'][0]).lower()
        assert "tayari" in err or "already" in err or "exist" in err

    def test_weak_password_rejected(self):
        data = {
            'email': 'weak@example.com',
            'full_name': 'Weak Password',
            'password': '123',
            'confirm_password': '123',
            'recaptcha_token': 'any-token',
        }

        # Assume recaptcha passes
        with patch('accounts.serializers.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {'success': True}
            serializer = RegisterSerializer(data=data)
            assert not serializer.is_valid()
            assert 'password' in serializer.errors

    def test_invalid_phone_number(self):
        data = {
            'email': 'badphone@example.com',
            'full_name': 'Phone Issue',
            'password': 'Strongpass123!',
            'confirm_password': 'Strongpass123!',
            'phone_number': '12',
            'recaptcha_token': 'any-token',
        }

        with patch('accounts.serializers.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {'success': True}
            serializer = RegisterSerializer(data=data)
            assert not serializer.is_valid()
            assert 'phone_number' in serializer.errors
            # Ujumbe wa Kiswahili: "Nambari ya simu ni fupi sana."
            assert 'fupi' in serializer.errors['phone_number'][0].lower()