# gov_integration/views/verification_request.py
from rest_framework import generics, permissions
from gov_integration.models import VerificationRequest
from gov_integration.serializers.service_type import VerificationRequestSerializer
from gov_integration.tasks import send_verification_request


class VerificationRequestCreateView(generics.CreateAPIView):
    queryset = VerificationRequest.objects.all()
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        institution = getattr(self.request, 'institution', None)
        instance = serializer.save(user=self.request.user, institution=institution)
        send_verification_request.delay(instance.id)