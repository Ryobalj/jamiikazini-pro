# kiini/mixins.py

from rest_framework import permissions

class InstitutionMixin:
    """
    Mixin ya kuhakikisha data zote zinafungwa kwenye taasisi ya mtumiaji.
    Inaweza kutumika kwenye List, Create, Update, Delete views.
    """

    def get_queryset(self):
        """
        Rudisha queryset iliyochujwa kwa institution ya mtumiaji.
        Lazima view iwe na 'queryset' au override hii vizuri.
        """
        queryset = super().get_queryset()
        user_institution = getattr(self.request.user, 'institution', None)
        if user_institution:
            return queryset.filter(institution=user_institution)
        return queryset.none()

    def perform_create(self, serializer):
        """
        Hakikisha record mpya inahusishwa na institution ya user.
        """
        institution = getattr(self.request.user, 'institution', None)
        if institution:
            serializer.save(institution=institution)
        else:
            raise permissions.PermissionDenied("You are not associated with any institution.")