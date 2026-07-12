# jamiiwallet/views/expense_views.py

from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from jamiiwallet.models.expense import Expense
from jamiiwallet.serializers.expense_serializer import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    """CRUD ya gharama - kila mtumiaji anaona/anasimamia za wallet yake mwenyewe."""
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['incurred_at', 'amount', 'created_at']
    ordering = ['-incurred_at']

    def get_queryset(self):
        if not hasattr(self.request.user, 'wallet'):
            return Expense.objects.none()
        return Expense.objects.filter(wallet=self.request.user.wallet)
