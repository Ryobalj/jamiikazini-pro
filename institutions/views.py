# institutions/views.py

from django.db.models import Q
from rest_framework import generics, permissions
from kiini.models.institution import Institution
from kiini.serializers.institution_serializers import InstitutionSerializer

class MyInstitutionsList(generics.ListAPIView):
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Sambamba na InstitutionViewSet.get_queryset - mwanachama (si
        # mmiliki tu) lazima aone taasisi yake, vinginevyo Step2InstitutionPicker
        # (inayotumia endpoint hii) haitaonyesha taasisi ya mfanyakazi.
        user = self.request.user
        q = Q(owner=user)
        if getattr(user, "institution_id", None):
            q |= Q(pk=user.institution_id)
        return Institution.objects.filter(q).distinct()

