from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

from django.utils import timezone
from jamiiwallet.models.wallet import Wallet
from decimal import Decimal, InvalidOperation

from payments.models.bulk_payment import (
    BulkPaymentTemplate,
    BulkPaymentExecution,
)
from payments.serializers.bulk_payment_serializer import (
    BulkPaymentTemplateSerializer,
    BulkPaymentTemplateSummarySerializer,
    BulkPaymentExecutionSerializer,
    BulkPaymentExecutionSummarySerializer,
    BulkPaymentExecutionCreateSerializer,
)


class BulkPaymentTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet ya kusimamia template za malipo mengi (BulkPaymentTemplate)
    - CRUD kamili
    - Muhtasari wa haraka
    - Imeunganishwa na user context
    """
    queryset = BulkPaymentTemplate.objects.all().select_related("created_by")
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Orodhesha templates zilizoundwa na user huyu pekee"""
        user = self.request.user
        return self.queryset.filter(created_by=user)

    def get_serializer_class(self):
        """Badilisha serializer kulingana na action"""
        if self.action == "list":
            return BulkPaymentTemplateSummarySerializer
        return BulkPaymentTemplateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"], url_path="executions")
    def executions(self, request, pk=None):
        """Orodhesha utekelezaji (executions) uliofanywa kwa template hii"""
        template = self.get_object()
        executions = (
            BulkPaymentExecution.objects.filter(template=template)
            .select_related("executed_by")
            .order_by("-executed_at")
        )
        serializer = BulkPaymentExecutionSummarySerializer(executions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BulkPaymentExecutionViewSet(viewsets.ModelViewSet):
    queryset = BulkPaymentExecution.objects.all()
    serializer_class = BulkPaymentExecutionSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        """Fanya utekelezaji halisi wa malipo mengi kwa kutumia wallet"""
        execution = serializer.save(executed_by=self.request.user)
        template = execution.template

        if not template or not template.payments_data:
            raise ValidationError({"template": _("Template haina malipo yoyote halali")})

        # 1️⃣ Pata wallet ya mtumiaji aliyeanzisha
        try:
            sender_wallet = Wallet.objects.select_for_update().get(owner=self.request.user)
        except Wallet.DoesNotExist:
            raise ValidationError(_("Wallet ya mtumiaji haipo"))

        total_amount = Decimal(str(template.total_amount or 0))
        if total_amount <= 0:
            raise ValidationError(_("Kiasi cha jumla lazima kiwe kikubwa kuliko sifuri"))

        # 2️⃣ Hakikisha ana salio la kutosha
        if sender_wallet.available_balance < total_amount:
            raise ValidationError(_("Salio halitoshi kufanya malipo yote ya batch"))

        results = []
        success_count = 0
        fail_count = 0

        for i, payment in enumerate(template.payments_data):
            recipient_id = payment.get("recipient_user_id")
            amount = payment.get("amount")
            try:
                amount = Decimal(str(amount))
                if amount <= 0:
                    raise ValueError("Kiasi kisicho halali")

                recipient_wallet = Wallet.objects.select_for_update().get(owner_id=recipient_id)

                # 3️⃣ Fanya uhamisho wa kweli (deduct + credit)
                sender_wallet.debit(amount, reference=f"BULK:{execution.id}")
                recipient_wallet.credit(amount, reference=f"BULK:{execution.id}")

                success_count += 1
                results.append({
                    "recipient_id": recipient_id,
                    "amount": float(amount),
                    "status": "success",
                })

            except Wallet.DoesNotExist:
                fail_count += 1
                results.append({
                    "recipient_id": recipient_id,
                    "amount": float(amount),
                    "status": "failed",
                    "error": "Wallet ya mpokeaji haijapatikana"
                })
            except (InvalidOperation, ValueError) as e:
                fail_count += 1
                results.append({
                    "recipient_id": recipient_id,
                    "amount": str(amount),
                    "status": "failed",
                    "error": str(e)
                })
            except Exception as e:
                fail_count += 1
                results.append({
                    "recipient_id": recipient_id,
                    "amount": str(amount),
                    "status": "failed",
                    "error": str(e)
                })

        # 4️⃣ Hifadhi matokeo ya mwisho
        execution.successful_count = success_count
        execution.failed_count = fail_count
        execution.results = results
        execution.completed_at = timezone.now()
        execution.status = (
            BulkPaymentExecution.Status.COMPLETED
            if fail_count == 0 else
            BulkPaymentExecution.Status.PARTIAL
            if success_count > 0 else
            BulkPaymentExecution.Status.FAILED
        )
        execution.save()

        # 5️⃣ Hifadhi mabadiliko ya wallet ya mtumaji
        sender_wallet.save(update_fields=["balance", "updated_at"])

        return execution