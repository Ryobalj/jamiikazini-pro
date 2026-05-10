# businesses/views/order_views.py

from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from businesses.models.order import Order
from businesses.serializers.order_serializer import OrderSerializer
from security.decorators import conditional_2fa_required


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD kwa Orders.

    Rules:
    - Superuser anaona na kuhariri orders zote
    - Institution admin / Provider anaona na kuhariri orders za biashara zake pekee
    - Client anaona na kuhariri orders alizoanzisha
    - Admin actions zinaweza kuhitaji 2FA
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        business_id = self.kwargs.get("business_pk")

        if user.is_superuser:
            qs = Order.objects.filter(business_id=business_id) if business_id else Order.objects.all()
        elif user.role in ["INSTITUTION_ADMIN", "PROVIDER"]:
            qs = Order.objects.filter(business__owner=user)
            if business_id:
                qs = qs.filter(business_id=business_id)
        else:  # Client
            qs = Order.objects.filter(client=user)
            if business_id:
                qs = qs.filter(business_id=business_id)
        return qs

    def perform_create(self, serializer):
        """
        Ruhusu client au admin kuunda order.
        Client lazima awe ni request.user.
        """
        serializer.save(client=self.request.user)

    @conditional_2fa_required(action_type="admin_action")
    def perform_update(self, serializer):
        order = serializer.instance
        user = self.request.user

        if user.is_superuser:
            serializer.save()
        elif user.role in ["INSTITUTION_ADMIN", "PROVIDER"]:
            if order.business.owner != user:
                raise PermissionDenied("Huwezi kuhariri order isiyo ya biashara yako.")
            serializer.save()
        elif order.client == user:
            serializer.save()
        else:
            raise PermissionDenied("Huwezi kuhariri order isiyo yako.")

    @conditional_2fa_required(action_type="admin_action")
    def perform_destroy(self, instance):
        user = self.request.user

        if user.is_superuser:
            instance.delete()
        elif user.role in ["INSTITUTION_ADMIN", "PROVIDER"]:
            if instance.business.owner != user:
                raise PermissionDenied("Huwezi kufuta order isiyo ya biashara yako.")
            instance.delete()
        elif instance.client == user:
            instance.delete()
        else:
            raise PermissionDenied("Huwezi kufuta order isiyo yako.")