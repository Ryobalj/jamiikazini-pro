import pytest
from accounts.models import User
from accounts.serializers import UserUpdateSerializer

@pytest.mark.django_db
def test_user_update_serializer_updates_full_name_and_phone_number():
    # Tengeneza user sample
    user = User.objects.create_user(
        email='test@example.com',
        password='password123',
        full_name='Old Name',
        role='CLIENT',
        phone_number='+255700000000'
    )
    
    data = {
        'full_name': 'New Name',
        'phone_number': '+255711111111',
        'email': 'shouldnotchange@example.com',  # should be ignored
        'role': 'ADMIN',  # should be ignored
    }

    serializer = UserUpdateSerializer(instance=user, data=data, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated_user = serializer.save()

    # Check fields updated correctly
    assert updated_user.full_name == 'New Name'
    assert updated_user.phone_number == '+255711111111'  # decrypted value checked
    assert updated_user.email == 'test@example.com'  # email not changed
    assert updated_user.role == 'CLIENT'  # role not changed

@pytest.mark.django_db
def test_user_update_serializer_allows_partial_update():
    user = User.objects.create_user(
        email='partial@example.com',
        password='password123',
        full_name='Partial Name',
        role='CLIENT',
    )

    data = {'full_name': 'Partial New Name'}
    serializer = UserUpdateSerializer(instance=user, data=data, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated_user = serializer.save()
    assert updated_user.full_name == 'Partial New Name'

@pytest.mark.django_db
def test_user_update_serializer_clears_phone_number():
    user = User.objects.create_user(
        email='clearphone@example.com',
        password='password123',
        full_name='Clear Phone',
        role='CLIENT',
        phone_number='+255700000001'
    )

    data = {'phone_number': ''}
    serializer = UserUpdateSerializer(instance=user, data=data, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated_user = serializer.save()
    assert updated_user.phone_number == ''