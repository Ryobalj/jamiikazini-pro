# security/helpers/encryption.py

import hashlib
import hmac

from cryptography.fernet import Fernet
from django.conf import settings

fernet = Fernet(settings.FERNET_SECRET_KEY)

def encrypt_data(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()

def decrypt_data(encrypted_text: str) -> str:
    return fernet.decrypt(encrypted_text.encode()).decode()

def hash_data(plain_text: str) -> str:
    """
    Deterministic keyed fingerprint (HMAC-SHA256) ya data nyeti - Fernet
    haitoi ciphertext ile ile mara mbili, hivyo kulinganisha/uniqueness
    (mf. NIDA/NIN moja = akaunti moja) kunahitaji hash hii badala yake.
    Value inanormalishwa (strip + upper) ili '  abc ' na 'ABC' zilingane.
    """
    normalized = plain_text.strip().upper()
    key = settings.FERNET_SECRET_KEY
    if isinstance(key, str):
        key = key.encode()
    return hmac.new(key, normalized.encode(), hashlib.sha256).hexdigest()