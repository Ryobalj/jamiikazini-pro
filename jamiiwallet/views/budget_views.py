# jamiiwallet/views/budget_views.py

from rest_framework import viewsets, permissions

from jamiiwallet.models.budget import Budget
from jamiiwallet.serializers.budget_serializer import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    """CRUD ya bajeti - kila mtumiaji anaona/anasimamia za wallet yake mwenyewe."""
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not hasattr(self.request.user, 'wallet'):
            return Budget.objects.none()
        return Budget.objects.filter(wallet=self.request.user.wallet)
