# savings/views/savings_views.py

import math
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from accounts.permissions import IsIdentityVerified
from payments.models.currency import Currency
from payments.services.currency_service import get_default_currency_code
from savings.models.savings_group import SavingsGroup
from savings.models.group_membership import GroupMembership, GroupMemberRole
from savings.models.group_wallet import GroupWallet
from savings.models.contribution import Contribution
from savings.models.withdrawal_request import WithdrawalRequest, WithdrawalRequestStatus
from savings.models.withdrawal_approval import WithdrawalApproval, WithdrawalDecision
from savings.serializers import (
    SavingsGroupSerializer,
    SavingsGroupCreateSerializer,
    JoinGroupSerializer,
    ContributeSerializer,
    ContributionSerializer,
    WithdrawalRequestSerializer,
    WithdrawalRequestCreateSerializer,
    VoteSerializer,
)
from savings.services.group_wallet_service import contribute as do_contribute, execute_withdrawal


class SavingsGroupViewSet(viewsets.ModelViewSet):
    """
    VICOBA/SACCOS - mfuko wa pamoja wa kikundi unaohitaji kura ya wanachama
    kabla ya kutoa fedha. IsIdentityVerified inalinda kila hatua inayohusisha
    fedha halisi (create/join/contribute/request-withdrawal) - kupiga kura tu
    hakuhitaji lango la ziada kwa sababu tayari ni mwanachama aliyethibitishwa.
    """
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("create", "join", "contribute", "request_withdrawal"):
            return [permissions.IsAuthenticated(), IsIdentityVerified()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return SavingsGroupCreateSerializer
        return SavingsGroupSerializer

    def get_queryset(self):
        return SavingsGroup.objects.filter(
            memberships__user=self.request.user, memberships__is_active=True
        ).distinct().select_related("wallet", "currency")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        currency = data.get("currency")
        if not currency:
            currency = Currency.objects.filter(code=get_default_currency_code()).first()
        if not currency:
            raise ValidationError({"currency": "Hakuna sarafu ya msingi iliyowekwa."})

        with db_transaction.atomic():
            group = SavingsGroup.objects.create(
                name=data["name"], created_by=request.user, currency=currency,
                approval_threshold_percent=data["approval_threshold_percent"],
            )
            GroupWallet.objects.create(group=group, currency=currency)
            GroupMembership.objects.create(group=group, user=request.user, role=GroupMemberRole.ADMIN)

        return Response(
            SavingsGroupSerializer(group, context={"request": request}).data, status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="join")
    def join(self, request):
        serializer = JoinGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["invite_code"].strip().upper()

        try:
            group = SavingsGroup.objects.get(invite_code=code, is_active=True)
        except SavingsGroup.DoesNotExist:
            raise NotFound("Msimbo huu wa mwaliko haupatikani.")

        membership, created = GroupMembership.objects.get_or_create(
            group=group, user=request.user,
            defaults={"contribution_amount": serializer.validated_data["contribution_amount"]},
        )
        if not created and not membership.is_active:
            membership.is_active = True
            membership.save(update_fields=["is_active", "updated_at"])

        return Response(SavingsGroupSerializer(group, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="contribute")
    @db_transaction.atomic
    def contribute(self, request, pk=None):
        group = self._get_membership_scoped_group(pk, request.user)
        serializer = ContributeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            contribution = do_contribute(
                group, request.user, serializer.validated_data["amount"],
                idempotency_key=f"group-contribute-{group.id}-{request.user.id}-{timezone.now().timestamp()}",
            )
        except DjangoValidationError as e:
            raise ValidationError({"detail": str(e.message) if hasattr(e, "message") else str(e)})

        return Response(ContributionSerializer(contribution).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="contributions")
    def contributions(self, request, pk=None):
        group = self._get_membership_scoped_group(pk, request.user)
        qs = group.contributions.select_related("member").order_by("-created_at")
        return Response(ContributionSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="withdrawal-requests")
    def withdrawal_requests_list(self, request, pk=None):
        group = self._get_membership_scoped_group(pk, request.user)
        qs = group.withdrawal_requests.select_related("requested_by").prefetch_related("approvals").order_by("-created_at")
        return Response(WithdrawalRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="request-withdrawal")
    def request_withdrawal(self, request, pk=None):
        group = self._get_membership_scoped_group(pk, request.user)

        serializer = WithdrawalRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        gw = GroupWallet.objects.get(group=group)
        if data["amount"] > gw.balance:
            raise ValidationError({"amount": "Kiasi kinachoombwa kinazidi salio la mfuko wa kikundi."})

        active_member_count = group.memberships.filter(is_active=True).count()
        required = math.ceil(
            (active_member_count * group.approval_threshold_percent) / Decimal("100")
        )
        required = max(1, int(required))

        wr = WithdrawalRequest.objects.create(
            group=group, requested_by=request.user, amount=data["amount"],
            purpose=data.get("purpose", ""), required_approval_count=required,
        )
        return Response(WithdrawalRequestSerializer(wr).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="vote-withdrawal")
    @db_transaction.atomic
    def vote_withdrawal(self, request, pk=None):
        group = self._get_membership_scoped_group(pk, request.user)

        request_id = request.data.get("request_id")
        if not request_id:
            raise ValidationError({"request_id": "Inahitajika."})

        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]

        try:
            wr = WithdrawalRequest.objects.select_for_update().get(pk=request_id, group=group)
        except WithdrawalRequest.DoesNotExist:
            raise NotFound("Ombi hili la kutoa fedha halipatikani.")
        if wr.status != WithdrawalRequestStatus.PENDING:
            raise ValidationError({"detail": "Ombi hili si PENDING tena."})

        WithdrawalApproval.objects.update_or_create(
            request=wr, member=request.user, defaults={"decision": decision},
        )

        approve_count = wr.approvals.filter(decision=WithdrawalDecision.APPROVE).count()
        reject_count = wr.approvals.filter(decision=WithdrawalDecision.REJECT).count()
        active_member_count = group.memberships.filter(is_active=True).count()

        if approve_count >= wr.required_approval_count:
            try:
                txn = execute_withdrawal(wr, idempotency_key=f"group-withdrawal-{wr.id}")
            except DjangoValidationError as e:
                raise ValidationError({"detail": str(e.message) if hasattr(e, "message") else str(e)})
            wr.status = WithdrawalRequestStatus.EXECUTED
            wr.destination_transaction = txn
            wr.executed_at = timezone.now()
            wr.save(update_fields=["status", "destination_transaction", "executed_at", "updated_at"])

            from kiini.helpers.notification_helper import notify_user
            from kiini.models.notification import NotificationType
            notify_user(
                wr.requested_by,
                f"Ombi lako la kutoa fedha kwenye kikundi '{group.name}' limeidhinishwa na kutekelezwa.",
                notification_type=NotificationType.PAYMENT,
                link=f"/savings/{group.id}",
            )
        elif reject_count > (active_member_count - wr.required_approval_count):
            # Idhini haiwezekani tena kihesabu - ombi limekufa.
            wr.status = WithdrawalRequestStatus.REJECTED
            wr.save(update_fields=["status", "updated_at"])

        return Response(WithdrawalRequestSerializer(wr).data)

    def _get_membership_scoped_group(self, pk, user):
        try:
            group = SavingsGroup.objects.get(pk=pk)
        except SavingsGroup.DoesNotExist:
            raise NotFound("Kikundi hakipatikani.")
        if not GroupMembership.objects.filter(group=group, user=user, is_active=True).exists():
            raise PermissionDenied("Wewe si mwanachama wa kikundi hiki.")
        return group
