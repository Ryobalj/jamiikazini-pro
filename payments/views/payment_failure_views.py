# payments/views/payment_failure_views.py

from rest_framework.decorators import action
from rest_framework.response import Response

from payments.models.payment_failure import PaymentFailure
from payments.serializers.payment_failure_serializer import (
    PaymentFailureSerializer,
    PaymentFailureSummarySerializer,
)
from payments.views.base import BaseReadOnlyViewSet


class PaymentFailureViewSet(BaseReadOnlyViewSet):
    """
    ViewSet ya Payment Failures:
    - Read-only: list & retrieve
    - Custom action: retry
    """
    queryset = PaymentFailure.objects.select_related("user", "currency").all()
    serializer_class = PaymentFailureSerializer
    ordering = ["-created_at"]  # sahihisha reference ya field

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentFailureSummarySerializer
        return super().get_serializer_class()

    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        failure = self.get_object()
        # Tumia method ya model kurekebisha retries
        failure.increment_retries()
        serializer = self.get_serializer(failure)
        return Response(serializer.data)