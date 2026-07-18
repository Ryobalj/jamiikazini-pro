# savings/serializers/savings_serializer.py

from decimal import Decimal
from rest_framework import serializers

from payments.models.currency import Currency
from savings.models.savings_group import SavingsGroup
from savings.models.group_membership import GroupMembership
from savings.models.group_wallet import GroupWallet
from savings.models.contribution import Contribution
from savings.models.withdrawal_request import WithdrawalRequest
from savings.models.withdrawal_approval import WithdrawalApproval


class GroupMembershipSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = GroupMembership
        fields = ["id", "user", "member_name", "role", "contribution_amount", "is_active", "created_at"]
        read_only_fields = fields


class SavingsGroupSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(source="wallet.balance", max_digits=16, decimal_places=2, read_only=True, default=Decimal("0.00"))
    currency_code = serializers.CharField(source="currency.code", read_only=True)
    member_count = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGroup
        fields = [
            "id", "name", "created_by", "invite_code", "currency", "currency_code",
            "approval_threshold_percent", "is_active", "balance", "member_count", "my_role", "created_at",
        ]
        read_only_fields = ["id", "created_by", "invite_code", "currency_code", "balance", "member_count", "my_role", "created_at"]

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.memberships.filter(user=request.user, is_active=True).first()
        return membership.role if membership else None


class SavingsGroupCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    currency = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all(), required=False)
    approval_threshold_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("1"), max_value=Decimal("100"), default=Decimal("51.00"),
    )


class JoinGroupSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=12)
    contribution_amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), default=Decimal("0.00"))


class ContributeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))


class ContributionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = Contribution
        fields = ["id", "member", "member_name", "amount", "created_at"]
        read_only_fields = fields


class WithdrawalRequestCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    purpose = serializers.CharField(required=False, allow_blank=True, default="")


class WithdrawalApprovalSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = WithdrawalApproval
        fields = ["id", "member", "member_name", "decision", "created_at"]
        read_only_fields = fields


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source="requested_by.full_name", read_only=True)
    approvals = WithdrawalApprovalSerializer(many=True, read_only=True)
    approve_count = serializers.SerializerMethodField()
    reject_count = serializers.SerializerMethodField()

    class Meta:
        model = WithdrawalRequest
        fields = [
            "id", "group", "requested_by", "requested_by_name", "amount", "purpose", "status",
            "required_approval_count", "approve_count", "reject_count", "approvals", "executed_at", "created_at",
        ]
        read_only_fields = fields

    def get_approve_count(self, obj):
        return obj.approvals.filter(decision="APPROVE").count()

    def get_reject_count(self, obj):
        return obj.approvals.filter(decision="REJECT").count()


class VoteSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
