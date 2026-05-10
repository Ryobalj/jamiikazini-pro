# businesses/views/product_order_views.py

from rest_framework import viewsets, permissions
from businesses.models.order import Order
from businesses.serializers.order_serializer import OrderSerializer


class ProductOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Soma Orders zote zinazohusisha Product fulani.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        product_id = self.kwargs["product_pk"]
        return Order.objects.filter(items__product_id=product_id).distinct()