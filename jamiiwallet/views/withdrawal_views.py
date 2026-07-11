# jamiiwallet/views/withdrawal_views.py

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError

from jamiiwallet.serializers.withdrawal_serializer import WithdrawalSerializer

logger = logging.getLogger(__name__)


class WithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'wallet'):
            logger.error(f'User {request.user.id} has no wallet.')
            return Response({'detail': 'User wallet not found.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = WithdrawalSerializer(data=request.data, context={'request': request})
        try:
            if serializer.is_valid(raise_exception=True):
                withdrawal = serializer.save(user=request.user)

                # NB: Withdrawal.save() already queues process_withdrawal_transaction

                logger.info(f'Withdrawal created with id {withdrawal.id} for user {request.user.id}')

                return Response({
                    'id': withdrawal.id,
                    'amount': withdrawal.amount,
                    'status': withdrawal.status,
                    'created_at': withdrawal.created_at,
                }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.warning(f'Validation error in withdrawal by user {request.user.id}: {e}')
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Unexpected error creating withdrawal for user {request.user.id}: {e}', exc_info=True)
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
