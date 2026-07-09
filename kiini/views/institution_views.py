# kiini/views/institution_views.py

from django.db.models import Q
from rest_framework import viewsets, permissions
from kiini.models.institution import Institution
from kiini.serializers.institution_serializers import InstitutionSerializer


class InstitutionViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Institution.objects.all()
        # Mtumiaji aone taasisi anazomiliki NA taasisi yake (uanachama) -
        # bila hili mwanachama hakuweza kuona taasisi yake mwenyewe
        q = Q(owner=user)
        if getattr(user, "institution_id", None):
            q |= Q(pk=user.institution_id)
        return Institution.objects.filter(q).distinct()

    def perform_create(self, serializer):
        institution = serializer.save(owner=self.request.user)
        
        # Set as user's primary institution if they don't have one
        user = self.request.user
        if not user.institution:
            user.institution = institution
            user.save(update_fields=['institution'])
        
        return institution