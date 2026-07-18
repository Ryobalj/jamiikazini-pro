from django.contrib import admin

from savings.models.savings_group import SavingsGroup
from savings.models.group_membership import GroupMembership
from savings.models.group_wallet import GroupWallet
from savings.models.contribution import Contribution
from savings.models.withdrawal_request import WithdrawalRequest
from savings.models.withdrawal_approval import WithdrawalApproval


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0


@admin.register(SavingsGroup)
class SavingsGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "invite_code", "created_by", "approval_threshold_percent", "is_active", "created_at")
    search_fields = ("name", "invite_code")
    inlines = [GroupMembershipInline]


@admin.register(GroupWallet)
class GroupWalletAdmin(admin.ModelAdmin):
    list_display = ("group", "balance", "currency")
    readonly_fields = ("group",)


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("group", "member", "amount", "created_at")
    readonly_fields = ("source_transaction",)


class WithdrawalApprovalInline(admin.TabularInline):
    model = WithdrawalApproval
    extra = 0


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("group", "requested_by", "amount", "status", "required_approval_count", "created_at")
    list_filter = ("status",)
    readonly_fields = ("destination_transaction",)
    inlines = [WithdrawalApprovalInline]
