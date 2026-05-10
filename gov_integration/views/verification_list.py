# gov_integration/views/verification_list.py
from rest_framework import generics, permissions
from gov_integration.models import VerificationRequest
from gov_integration.serializers.service_type import VerificationRequestSerializer


class VerificationRequestListView(generics.ListAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        institution = getattr(self.request, 'institution', None)

        if user.role == 'ADMIN':
            return VerificationRequest.objects.all()

        return VerificationRequest.objects.filter(user=user, institution=institution)