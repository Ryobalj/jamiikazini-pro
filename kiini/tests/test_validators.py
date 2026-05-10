# tests/test_validators.py

import pytest
from kiini.helpers.validators import validate_eac_phone
from django.core.exceptions import ValidationError

def test_valid_eac_phone():
    assert validate_eac_phone('+255712345678') is None
    assert validate_eac_phone('+256712345678') is None

def test_invalid_eac_phone():
    with pytest.raises(ValidationError):
        validate_eac_phone('+49...')  # Germany