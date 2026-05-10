# security/tests/test_encryption.py

import pytest
from security.helpers.encryption import encrypt_data, decrypt_data

def test_encrypt_decrypt():
    original_text = "siri sana 123456!@#"
    encrypted_text = encrypt_data(original_text)

    # Hakikisha encrypted text ni string na sio original
    assert isinstance(encrypted_text, str)
    assert encrypted_text != original_text

    # Decrypt encrypted text na hakikisha inarudi kama original
    decrypted_text = decrypt_data(encrypted_text)
    assert decrypted_text == original_text

@pytest.mark.parametrize("text", [
    "",
    " ",
    "some normal text",
    "😊 unicode test 🚀",
    "1234567890",
])
def test_encrypt_decrypt_various_inputs(text):
    encrypted = encrypt_data(text)
    decrypted = decrypt_data(encrypted)
    assert decrypted == text