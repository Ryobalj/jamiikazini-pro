# accounts/tests/test_permissions/test_is_identity_verified.py
#
# IsIdentityVerified is now a dual gate: NIDA (is_identity_verified) AND
# phone OTP (is_phone_verified), mirroring email verification's now-symmetric
# phone counterpart. A user verified on only one side must still be blocked.

import pytest
from unittest.mock import Mock

from accounts.permissions import IsIdentityVerified

pytestmark = pytest.mark.django_db


def _request(user):
    return Mock(user=user)


def test_blocks_when_neither_verified(user_factory):
    user = user_factory(is_identity_verified=False, is_phone_verified=False)
    assert IsIdentityVerified().has_permission(_request(user), None) is False


def test_blocks_when_only_nida_verified(user_factory):
    user = user_factory(is_identity_verified=True, is_phone_verified=False)
    assert IsIdentityVerified().has_permission(_request(user), None) is False


def test_blocks_when_only_phone_verified(user_factory):
    user = user_factory(is_identity_verified=False, is_phone_verified=True)
    assert IsIdentityVerified().has_permission(_request(user), None) is False


def test_allows_when_both_verified(user_factory):
    user = user_factory(is_identity_verified=True, is_phone_verified=True)
    assert IsIdentityVerified().has_permission(_request(user), None) is True
