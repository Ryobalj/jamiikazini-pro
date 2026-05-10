# payments/views/base.py

from rest_framework import viewsets, permissions, mixins, status
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

class BaseReadOnlyViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    """
    Base viewset that includes ONLY retrieve and list actions by default.
    Can be extended for custom create/update operations.
    """
    
    def create(self, request, *args, **kwargs):
        """
        Allow creation if explicitly implemented in child classes.
        """
        # Check if child class has implemented create logic
        if hasattr(self, 'perform_create') or hasattr(super(), 'create'):
            return super().create(request, *args, **kwargs)
        else:
            return Response(
                {"detail": _("Method not allowed.")},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

class BaseCRUDViewSet(viewsets.ModelViewSet):
    """
    Base CRUD viewset kwa DRY pattern.
    - Auto filter_backends, ordering
    - Auto-detect owner/created_by/last_modified_by kama model inazo
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = []
    ordering_fields = []
    ordering = ["-id"]

    # override hii kwa force kama hutaki auto-detection
    owner_field = "owner"

    def _get_model(self):
        """Helper kupata model kutoka serializer."""
        return getattr(self.get_serializer().Meta, "model", None)

    def get_queryset(self):
        """
        Restrict queryset by owner kama model ina hiyo field.
        """
        qs = super().get_queryset()
        model = self._get_model()
        user = getattr(self.request, "user", None)

        if not model or not user or not user.is_authenticated:
            return qs

        # check kama model ina owner_field
        if self.owner_field and hasattr(model, self.owner_field):
            return qs.filter(**{self.owner_field: user})

        return qs

    def perform_create(self, serializer):
        """
        Auto-set owner/created_by/last_modified_by kama zipo kwenye model.
        """
        model = serializer.Meta.model
        user = getattr(self.request, "user", None)
        extra = {}

        if user and user.is_authenticated:
            if self.owner_field and hasattr(model, self.owner_field):
                extra[self.owner_field] = user
            if hasattr(model, "created_by"):
                extra["created_by"] = user
            if hasattr(model, "last_modified_by"):
                extra["last_modified_by"] = user

        serializer.save(**extra)

    def perform_update(self, serializer):
        """
        Auto-set last_modified_by kama ipo kwenye model.
        """
        model = serializer.Meta.model
        user = getattr(self.request, "user", None)
        extra = {}

        if user and user.is_authenticated and hasattr(model, "last_modified_by"):
            extra["last_modified_by"] = user

        serializer.save(**extra)