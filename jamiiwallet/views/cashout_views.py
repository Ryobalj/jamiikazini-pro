# jamiiwallet/views/cashout_views.py

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError

from jamiiwallet.serializers.cashout_serializer import CashOutSerializer

logger = logging.getLogger(__name__)


class CashOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'wallet'):
            logger.error(f'User {request.user.id} has no wallet.')
            return Response({'detail': 'User wallet not found.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CashOutSerializer(data=request.data, context={'request': request})
        try:
            if serializer.is_valid(raise_exception=True):
                transfer = serializer.save()

                # NB: Transfer.save() already queues process_transfer_transaction.
                # In CELERY_TASK_ALWAYS_EAGER mode this runs synchronously against a
                # separate DB fetch, so refresh to reflect the final status/reference.
                transfer.refresh_from_db()

                logger.info(f'Cash-out transfer created with id {transfer.id} for user {request.user.id}')

                return Response({
                    'id': transfer.id,
                    'amount': transfer.amount,
                    'business_name': transfer.recipient.full_name,
                    'reference': transfer.reference,
                    'status': transfer.status,
                    'created_at': transfer.created_at,
                }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.warning(f'Validation error in cash-out by user {request.user.id}: {e}')
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Unexpected error creating cash-out for user {request.user.id}: {e}', exc_info=True)
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
