import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from accounts.serializers import PasswordChangeSerializer
from rest_framework.test import APIRequestFactory

User = get_user_model()

@pytest.mark.django_db
def test_password_change_serializer_accepts_correct_old_password_and_valid_new():
    user = User.objects.create_user(
        email='user@example.com',
        password='Oldpass123!',
        full_name='Test User',
        role='CLIENT'
    )

    factory = APIRequestFactory()
    request = factory.post('/dummy-url/')
    request.user = user

    data = {
        'old_password': 'Oldpass123!',
        'new_password': 'Newpass123!'
    }
    serializer = PasswordChangeSerializer(data=data, context={'request': request})
    assert serializer.is_valid()


@pytest.mark.django_db
def test_password_change_serializer_rejects_wrong_old_password():
    user = User.objects.create_user(
        email='user2@example.com',
        password='Oldpass123!',
        full_name='Test User',
        role='CLIENT'
    )

    factory = APIRequestFactory()
    request = factory.post('/dummy-url/')
    request.user = user

    data = {
        'old_password': 'WrongOld123!',
        'new_password': 'Newpass123!'
    }
    serializer = PasswordChangeSerializer(data=data, context={'request': request})
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_password_change_serializer_rejects_weak_new_password():
    user = User.objects.create_user(
        email='user3@example.com',
        password='Oldpass123!',
        full_name='Test User',
        role='CLIENT'
    )

    factory = APIRequestFactory()
    request = factory.post('/dummy-url/')
    request.user = user

    data = {
        'old_password': 'Oldpass123!',
        'new_password': 'short'
    }
    serializer = PasswordChangeSerializer(data=data, context={'request': request})
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)