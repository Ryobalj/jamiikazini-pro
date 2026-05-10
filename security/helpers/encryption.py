# security/helpers/encryption.py

from cryptography.fernet import Fernet
from django.conf import settings

fernet = Fernet(settings.FERNET_SECRET_KEY)

def encrypt_data(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()

def decrypt_data(encrypted_text: str) -> str:
    return fernet.decrypt(encrypted_text.encode()).decode()