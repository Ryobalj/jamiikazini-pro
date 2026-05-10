# payments/views/payment_link_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.utils import timezone
from payments.models.payment_link import PaymentLink
from payments.serializers.payment_link_serializer import PaymentLinkSerializer
from payments.services.payment_link_service import PaymentLinkService
import logging

logger = logging.getLogger(__name__)

class PaymentLinkViewSet(viewsets.ModelViewSet):
    """ViewSet kamili ya Payment Links"""
    serializer_class = PaymentLinkSerializer
    queryset = PaymentLink.objects.all()

    def get_queryset(self):
        user = self.request.user
        return PaymentLink.objects.filter(created_by=user).order_by('-created_at')

    def perform_create(self, serializer):
        service = PaymentLinkService()
        try:
            link = service.create_payment_link(
                user=self.request.user,
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data['currency'],
                description=serializer.validated_data.get('description', ''),
                expires_in_days=serializer.validated_data.get('expires_at', 7),
                allowed_methods=serializer.validated_data.get('allowed_methods', None),
                metadata=serializer.validated_data.get('metadata', None)
            )
            serializer.instance = link
        except Exception as e:
            logger.error(f"Failed to create payment link: {e}")
            raise ValidationError(str(e))

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        service = PaymentLinkService()
        link = self.get_object()
        payment_method = request.data.get('payment_method')
        try:
            result = service.process_payment_link(
                link_code=link.link_code,
                user=request.user,
                payment_method=payment_method,
                metadata=request.data.get('metadata', None)
            )
            return Response(result)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing payment link {link.link_code}: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        service = PaymentLinkService()
        link = self.get_object()
        new_expires_at = request.data.get('expires_at')
        if not new_expires_at:
            return Response({'error': 'New expiry date required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_expires_at = timezone.datetime.fromisoformat(new_expires_at)
            extended = service.extend_payment_link(
                link_code=link.link_code,
                new_expires_at=new_expires_at,
                user=request.user
            )
            serializer = self.get_serializer(extended)
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Failed to extend payment link {link.link_code}: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)