# businesses/views/category_views.py

from rest_framework import viewsets, permissions
from businesses.models.category import BusinessCategory
from businesses.serializers.category_serializer import BusinessCategorySerializer
from security.decorators import conditional_2fa_required


class BusinessCategoryViewSet(viewsets.ModelViewSet):
    queryset = BusinessCategory.objects.all()
    serializer_class = BusinessCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    @conditional_2fa_required(action_type="admin_action")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @conditional_2fa_required(action_type="admin_action")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @conditional_2fa_required(action_type="admin_action")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @conditional_2fa_required(action_type="admin_action")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)