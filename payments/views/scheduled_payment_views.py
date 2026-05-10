# payments/views/scheduled_payment_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from payments.models.scheduled_payment import ScheduledPayment
from payments.serializers.scheduled_payment_serializer import ScheduledPaymentSerializer
from payments.services.scheduled_payment_service import ScheduledPaymentService
import logging

logger = logging.getLogger(__name__)

class ScheduledPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet kamili ya Scheduled Payments"""
    serializer_class = ScheduledPaymentSerializer
    queryset = ScheduledPayment.objects.all()

    def get_queryset(self):
        user = self.request.user
        return ScheduledPayment.objects.filter(created_by=user).order_by('-schedule_date')

    def perform_create(self, serializer):
        service = ScheduledPaymentService()
        try:
            scheduled = service.create_scheduled_payment(
                user=self.request.user,
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data['currency'],
                payment_method=serializer.validated_data['payment_method'],
                recipient_user=serializer.validated_data['recipient_user'],
                schedule_date=serializer.validated_data['schedule_date'],
                description=serializer.validated_data.get('description', ''),
                metadata=serializer.validated_data.get('metadata', None)
            )
            serializer.instance = scheduled
        except Exception as e:
            logger.error(f"Failed to create scheduled payment: {e}")
            raise ValidationError(str(e))

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        service = ScheduledPaymentService()
        payment = self.get_object()
        try:
            cancelled = service.cancel_scheduled_payment(payment.id, request.user)
            serializer = self.get_serializer(cancelled)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Failed to cancel scheduled payment {payment.id}: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)