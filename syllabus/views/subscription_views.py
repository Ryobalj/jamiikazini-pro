# syllabus/views/subscription_views.py

import logging
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.services.subscription_service import (
    get_or_create_subscription,
    charge_subscription,
)

logger = logging.getLogger(__name__)

# ADMIN-only test-price charge, so the whole buy -> insufficient-balance ->
# deposit -> resume flow can be verified end-to-end without spending the
# real monthly fee. Never applies to any other role.
ADMIN_TEST_PRICE = Decimal("100.00")


class SubscriptionStatusAPIView(APIView):
    """
    GET  -> current subscription status for the logged-in teacher's active
            workstation (whether they have full document-download access).
    POST -> subscribe now / renew now: attempts to debit the monthly fee
            immediately from the teacher's JamiiWallet balance, rather than
            waiting for the nightly renewal task.
    """
    permission_classes = [IsAuthenticated]

    def _get_workstation(self, request):
        return TeacherWorkStation.objects.filter(
            teacher=request.user, is_active=True
        ).first()

    def get(self, request):
        workstation = self._get_workstation(request)
        if not workstation:
            return Response(
                {"detail": "Hakuna workstation iliyosajiliwa."},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription = get_or_create_subscription(workstation)
        return Response({
            "is_valid": subscription.is_valid,
            "is_active": subscription.is_active,
            "monthly_fee": str(subscription.monthly_fee),
            "current_period_end": subscription.current_period_end,
            "last_charge_status": subscription.last_charge_status,
            "last_failure_reason": subscription.last_failure_reason,
        })

    def post(self, request):
        workstation = self._get_workstation(request)
        if not workstation:
            return Response(
                {"detail": "Hakuna workstation iliyosajiliwa."},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription = get_or_create_subscription(workstation)

        use_test_price = bool(request.data.get("admin_test_price")) and request.user.role == "ADMIN"
        amount_override = ADMIN_TEST_PRICE if use_test_price else None
        amount_needed = amount_override if amount_override is not None else subscription.monthly_fee

        success = charge_subscription(subscription, amount_override=amount_override)

        if not success:
            return Response(
                {
                    "detail": "Malipo hayajafanikiwa. Hakikisha salio la Wallet yako linatosha kisha jaribu tena.",
                    "last_failure_reason": subscription.last_failure_reason,
                    "amount_needed": str(amount_needed),
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        return Response({
            "detail": "Usajili umefanikiwa.",
            "is_valid": subscription.is_valid,
            "current_period_end": subscription.current_period_end,
            "amount_charged": str(amount_needed),
        }, status=status.HTTP_200_OK)
