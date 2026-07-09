from rest_framework import generics, status
from rest_framework.response import Response
from gov_integration.models import VerificationRequest
from gov_integration.serializers.service_type import VerificationRequestSerializer
from kiini.permissions.access import IsVerificationOwnerOrInstitutionAdmin


class VerificationStatusUpdateView(generics.UpdateAPIView):
    """
    Ruhusu mabadiliko ya status ya verification request
    kwa admin wa taasisi au user aliyeianzisha.
    """
    queryset = VerificationRequest.objects.all()
    # serializer_class inahitajika ili schema-generation (drf_yasg) isivunjike,
    # japo partial_update hushughulikia status yenyewe
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsVerificationOwnerOrInstitutionAdmin]
    lookup_url_kwarg = 'request_id'

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()  # Automatically applies object-level permission

        new_status = request.data.get('status')
        valid_statuses = ['PENDING', 'VERIFIED', 'FAILED']

        if new_status not in valid_statuses:
            return Response(
                {'detail': f'Invalid status. Must be one of: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = new_status
        instance.save()

        return Response(
            {'detail': f'Status updated to {new_status}.'},
            status=status.HTTP_200_OK
        )