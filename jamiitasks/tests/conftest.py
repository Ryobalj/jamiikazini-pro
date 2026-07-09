# jamiitasks/tests/conftest.py

import pytest


@pytest.fixture
def business_user(user_factory):
    """A provider-role user for wallet/payment tests."""
    return user_factory(role="PROVIDER", full_name="Business User")
