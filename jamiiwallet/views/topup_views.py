# jamiiwallet/views/topup_views.py

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError

from jamiiwallet.models.topup import TopUp
from jamiiwallet.serializers.topup_serializer import TopUpSerializer
from jamiitasks.tasks.wallet import confirm_topup_transaction

logger = logging.getLogger(__name__)

class TopUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = TopUpSerializer(data=request.data, context={'request': request})
        if not hasattr(request.user, 'wallet'):
            logger.error(f'User {request.user.id} has no wallet.')
            return Response({'detail': 'User wallet not found.'}, status=status.HTTP_400_BAD_REQUEST)

        user_wallet = request.user.wallet

        try:
            if serializer.is_valid(raise_exception=True):
                topup = serializer.save(user=request.user)

                # NB: TopUp.save() already queues confirm_topup_transaction

                logger.info(f'Topup created with id {topup.id} for user {request.user.id}')

                return Response({
                    'id': topup.id,
                    'amount': topup.amount,
                    'status': topup.status,
                    'created_at': topup.created_at,
                }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.warning(f'Validation error in topup by user {request.user.id}: {e}')
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Unexpected error creating topup for user {request.user.id}: {e}', exc_info=True)
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)