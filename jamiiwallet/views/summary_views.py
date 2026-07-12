# jamiiwallet/views/summary_views.py

from datetime import datetime

from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.expense import Expense, ExpenseCategory
from jamiiwallet.models.budget import Budget
from jamiiwallet.serializers.budget_serializer import BudgetSerializer


class WalletSummaryView(APIView):
    """
    Muhtasari wa hesabu za wallet: mapato (kutoka Transaction - COMPLETED
    tu, zinazoongeza salio) na matumizi (kutoka Expense zilizoandikwa),
    kwa kipindi cha tarehe (?start=YYYY-MM-DD&end=YYYY-MM-DD, default mwezi
    huu), pamoja na hali ya bajeti zinazoendelea.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'wallet'):
            return Response({'detail': 'Wallet haijapatikana.'}, status=400)
        wallet = request.user.wallet

        today = timezone.now().date()
        start = self._parse_date(request.query_params.get('start')) or today.replace(day=1)
        end = self._parse_date(request.query_params.get('end')) or today

        # Mapato: Transaction inayoongeza salio la wallet hii (TOP_UP, REFUND,
        # au TRANSFER ambapo huyu ndiye mpokeaji - initiated_by != wallet owner)
        income_qs = Transaction.objects.filter(
            wallet=wallet,
            status=Transaction.TransactionStatus.COMPLETED,
            created_at__date__gte=start,
            created_at__date__lte=end,
        ).filter(
            Q(transaction_type__in=[Transaction.TransactionType.TOP_UP, Transaction.TransactionType.REFUND])
            | Q(transaction_type=Transaction.TransactionType.TRANSFER, counterparty__isnull=False)
              & ~Q(initiated_by_id=wallet.user_id)
        )
        total_income = income_qs.aggregate(total=Sum('amount'))['total'] or 0

        expense_qs = Expense.objects.filter(wallet=wallet, incurred_at__gte=start, incurred_at__lte=end)
        total_expense = expense_qs.aggregate(total=Sum('amount'))['total'] or 0

        by_category = list(
            expense_qs.values('category').annotate(total=Sum('amount')).order_by('-total')
        )
        for row in by_category:
            row['category_display'] = ExpenseCategory(row['category']).label

        budgets = Budget.objects.filter(wallet=wallet, is_active=True)

        return Response({
            'start': start,
            'end': end,
            'total_income': total_income,
            'total_expense': total_expense,
            'net': total_income - total_expense,
            'by_category': by_category,
            'budgets': BudgetSerializer(budgets, many=True).data,
        })

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
