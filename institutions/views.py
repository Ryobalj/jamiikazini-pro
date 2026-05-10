# institutions/views.py

from rest_framework import generics, permissions
from kiini.models.institution import Institution
from kiini.serializers.institution_serializers import InstitutionSerializer

class MyInstitutionsList(generics.ListAPIView):
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Institution.objects.filter(owner=self.request.user)

