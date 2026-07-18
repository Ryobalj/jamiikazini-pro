# businesses/views/product_category_views.py

from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter
from businesses.models.product_category import ProductCategory
from businesses.serializers.product_category_serializer import ProductCategorySerializer
from security.decorators import conditional_2fa_required


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"
    search_fields = ['name']
    filter_backends = [OrderingFilter]
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
