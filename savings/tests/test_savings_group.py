# savings/tests/test_savings_group.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from payments.models.currency import Currency
from savings.models.savings_group import SavingsGroup
from savings.models.group_membership import GroupMembership, GroupMemberRole
from savings.models.group_wallet import GroupWallet
from savings.models.withdrawal_request import WithdrawalRequest, WithdrawalRequestStatus

pytestmark = pytest.mark.django_db

GROUPS_URL = "/api/v1/savings/groups/"


@pytest.fixture
def tzs(db):
    return Currency.objects.get_or_create(code="TZS")[0]


def _verified_user(user_factory, balance="1000000.00"):
    user = user_factory(role="CLIENT")
    user.is_identity_verified = True
    user.is_phone_verified = True
    user.save(update_fields=["is_identity_verified", "is_phone_verified"])
    user.wallet.balance = Decimal(balance)
    user.wallet.save(update_fields=["balance"])
    return user


@pytest.fixture
def admin_user(user_factory, tzs):
    return _verified_user(user_factory)


class TestCreateGroup:
    def test_requires_identity_verification(self, user_factory, tzs):
        unverified = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=unverified)
        response = api.post(GROUPS_URL, {"name": "VICOBA Wanawake"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_user_creates_group_with_wallet_and_admin_membership(self, admin_user):
        api = APIClient()
        api.force_authenticate(user=admin_user)
        response = api.post(GROUPS_URL, {"name": "VICOBA Wanawake", "approval_threshold_percent": "51.00"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        group = SavingsGroup.objects.get(id=response.data["id"])
        assert GroupWallet.objects.filter(group=group).exists()
        membership = GroupMembership.objects.get(group=group, user=admin_user)
        assert membership.role == GroupMemberRole.ADMIN
        assert response.data["invite_code"]
        assert response.data["balance"] == "0.00"


class TestJoinGroup:
    def _create_group(self, admin_user):
        api = APIClient()
        api.force_authenticate(user=admin_user)
        res = api.post(GROUPS_URL, {"name": "VICOBA"}, format="json")
        return res.data["invite_code"], res.data["id"]

    def test_verified_user_joins_via_invite_code(self, admin_user, user_factory, tzs):
        invite_code, group_id = self._create_group(admin_user)
        member = _verified_user(user_factory)

        api = APIClient()
        api.force_authenticate(user=member)
        response = api.post(f"{GROUPS_URL}join/", {"invite_code": invite_code}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert GroupMembership.objects.filter(group_id=group_id, user=member, is_active=True).exists()

    def test_invalid_invite_code_rejected(self, admin_user, user_factory, tzs):
        self._create_group(admin_user)
        member = _verified_user(user_factory)
        api = APIClient()
        api.force_authenticate(user=member)
        response = api.post(f"{GROUPS_URL}join/", {"invite_code": "BADCODE1"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_join_requires_identity_verification(self, admin_user, user_factory, tzs):
        invite_code, _ = self._create_group(admin_user)
        unverified = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=unverified)
        response = api.post(f"{GROUPS_URL}join/", {"invite_code": invite_code}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestContribute:
    def _group_with_members(self, admin_user, user_factory, tzs, n_members=1):
        api = APIClient()
        api.force_authenticate(user=admin_user)
        res = api.post(GROUPS_URL, {"name": "VICOBA"}, format="json")
        group_id, invite_code = res.data["id"], res.data["invite_code"]

        members = []
        for _ in range(n_members):
            m = _verified_user(user_factory)
            api.force_authenticate(user=m)
            api.post(f"{GROUPS_URL}join/", {"invite_code": invite_code}, format="json")
            members.append(m)
        return group_id, members

    def test_contribution_debits_member_wallet_and_credits_group_wallet(self, admin_user, user_factory, tzs):
        group_id, _ = self._group_with_members(admin_user, user_factory, tzs)
        api = APIClient()
        api.force_authenticate(user=admin_user)
        response = api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": "50000.00"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        admin_user.wallet.refresh_from_db()
        assert admin_user.wallet.balance == Decimal("950000.00")

        gw = GroupWallet.objects.get(group_id=group_id)
        assert gw.balance == Decimal("50000.00")

    def test_multiple_members_contributing_accumulate_correctly(self, admin_user, user_factory, tzs):
        group_id, members = self._group_with_members(admin_user, user_factory, tzs, n_members=2)
        api = APIClient()

        api.force_authenticate(user=admin_user)
        api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": "30000.00"}, format="json")
        api.force_authenticate(user=members[0])
        api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": "20000.00"}, format="json")
        api.force_authenticate(user=members[1])
        api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": "10000.00"}, format="json")

        gw = GroupWallet.objects.get(group_id=group_id)
        assert gw.balance == Decimal("60000.00")

    def test_contribution_fails_with_insufficient_balance(self, admin_user, user_factory, tzs):
        group_id, _ = self._group_with_members(admin_user, user_factory, tzs)
        api = APIClient()
        api.force_authenticate(user=admin_user)
        response = api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": "5000000.00"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        gw = GroupWallet.objects.get(group_id=group_id)
        assert gw.balance == Decimal("0.00")

    def test_non_member_cannot_contribute(self, admin_user, user_factory, tzs):
        group_id, _ = self._group_with_members(admin_user, user_factory, tzs)
        stranger = _verified_user(user_factory)
        api = APIClient()
        api.force_authenticate(user=stranger)
        response = api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": "1000.00"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWithdrawalVoting:
    def _funded_group(self, admin_user, user_factory, tzs, n_members=3, contribution="100000.00"):
        """Kikundi cha wanachama 4 (admin + 3), kila mmoja kachangia - jumla
        4 x contribution kwenye GroupWallet."""
        api = APIClient()
        api.force_authenticate(user=admin_user)
        res = api.post(GROUPS_URL, {"name": "VICOBA", "approval_threshold_percent": "51.00"}, format="json")
        group_id, invite_code = res.data["id"], res.data["invite_code"]
        api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": contribution}, format="json")

        members = [admin_user]
        for _ in range(n_members):
            m = _verified_user(user_factory)
            api.force_authenticate(user=m)
            api.post(f"{GROUPS_URL}{group_id}/join/", {"invite_code": invite_code}, format="json") if False else None
            api.post(f"{GROUPS_URL}join/", {"invite_code": invite_code}, format="json")
            api.post(f"{GROUPS_URL}{group_id}/contribute/", {"amount": contribution}, format="json")
            members.append(m)
        return group_id, members

    def test_withdrawal_executes_once_quorum_reached(self, admin_user, user_factory, tzs):
        # 4 members total, threshold 51% -> required = ceil(4*0.51) = 3
        group_id, members = self._funded_group(admin_user, user_factory, tzs)
        api = APIClient()
        requester = members[0]

        api.force_authenticate(user=requester)
        res = api.post(f"{GROUPS_URL}{group_id}/request-withdrawal/", {
            "amount": "150000.00", "purpose": "Kununua mbegu",
        }, format="json")
        assert res.status_code == status.HTTP_201_CREATED, res.data
        assert res.data["required_approval_count"] == 3
        request_id = res.data["id"]

        # 2 approvals - not enough yet
        for voter in members[:2]:
            api.force_authenticate(user=voter)
            vote_res = api.post(f"{GROUPS_URL}{group_id}/vote-withdrawal/", {
                "request_id": request_id, "decision": "APPROVE",
            }, format="json")
        assert vote_res.data["status"] == WithdrawalRequestStatus.PENDING

        gw_before = GroupWallet.objects.get(group_id=group_id).balance
        assert gw_before == Decimal("400000.00")

        # 3rd approval reaches quorum -> auto-executes
        api.force_authenticate(user=members[2])
        final_res = api.post(f"{GROUPS_URL}{group_id}/vote-withdrawal/", {
            "request_id": request_id, "decision": "APPROVE",
        }, format="json")
        assert final_res.data["status"] == WithdrawalRequestStatus.EXECUTED

        requester.wallet.refresh_from_db()
        gw_after = GroupWallet.objects.get(group_id=group_id)
        assert gw_after.balance == Decimal("250000.00")  # 400,000 - 150,000
        # requester's personal wallet: started at 1,000,000, contributed 100,000 (900,000), then received 150,000 back
        assert requester.wallet.balance == Decimal("900000.00") + Decimal("150000.00")

    def test_withdrawal_rejected_when_quorum_mathematically_impossible(self, admin_user, user_factory, tzs):
        group_id, members = self._funded_group(admin_user, user_factory, tzs)
        api = APIClient()
        api.force_authenticate(user=members[0])
        res = api.post(f"{GROUPS_URL}{group_id}/request-withdrawal/", {"amount": "50000.00"}, format="json")
        request_id = res.data["id"]
        assert res.data["required_approval_count"] == 3

        # 4 members total; 2 rejections means only 2 could still approve (< 3 required) -> impossible.
        for voter in members[1:3]:
            api.force_authenticate(user=voter)
            reject_res = api.post(f"{GROUPS_URL}{group_id}/vote-withdrawal/", {
                "request_id": request_id, "decision": "REJECT",
            }, format="json")

        assert reject_res.data["status"] == WithdrawalRequestStatus.REJECTED
        gw = GroupWallet.objects.get(group_id=group_id)
        assert gw.balance == Decimal("400000.00")  # untouched

    def test_withdrawal_exceeding_balance_rejected_at_creation(self, admin_user, user_factory, tzs):
        group_id, members = self._funded_group(admin_user, user_factory, tzs)
        api = APIClient()
        api.force_authenticate(user=members[0])
        response = api.post(f"{GROUPS_URL}{group_id}/request-withdrawal/", {"amount": "999999999.00"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_member_can_change_vote_before_execution(self, admin_user, user_factory, tzs):
        group_id, members = self._funded_group(admin_user, user_factory, tzs)
        api = APIClient()
        api.force_authenticate(user=members[0])
        res = api.post(f"{GROUPS_URL}{group_id}/request-withdrawal/", {"amount": "10000.00"}, format="json")
        request_id = res.data["id"]

        api.force_authenticate(user=members[1])
        api.post(f"{GROUPS_URL}{group_id}/vote-withdrawal/", {"request_id": request_id, "decision": "REJECT"}, format="json")
        change_res = api.post(f"{GROUPS_URL}{group_id}/vote-withdrawal/", {"request_id": request_id, "decision": "APPROVE"}, format="json")

        assert change_res.data["approve_count"] == 1
        assert change_res.data["reject_count"] == 0

    def test_non_member_cannot_vote(self, admin_user, user_factory, tzs):
        group_id, members = self._funded_group(admin_user, user_factory, tzs)
        api = APIClient()
        api.force_authenticate(user=members[0])
        res = api.post(f"{GROUPS_URL}{group_id}/request-withdrawal/", {"amount": "10000.00"}, format="json")
        request_id = res.data["id"]

        stranger = _verified_user(user_factory)
        api.force_authenticate(user=stranger)
        response = api.post(f"{GROUPS_URL}{group_id}/vote-withdrawal/", {"request_id": request_id, "decision": "APPROVE"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
