# jamiiwallet/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from jamiiwallet.views.transaction_views import TransactionViewSet, CreateTransactionAPIView
from jamiiwallet.views.wallet_views import WalletDetailView
from jamiiwallet.views.topup_views import TopUpView
from jamiiwallet.views.withdrawal_views import WithdrawalView
from jamiiwallet.views.transfer_views import TransferView
from jamiiwallet.views.payment_request_views import PaymentRequestViewSet
from jamiiwallet.views.beneficiary_views import BeneficiaryViewSet
from jamiiwallet.views.expense_views import ExpenseViewSet
from jamiiwallet.views.budget_views import BudgetViewSet
from jamiiwallet.views.summary_views import WalletSummaryView

app_name = 'wallet'

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'requests', PaymentRequestViewSet, basename='payment-request')
router.register(r'beneficiaries', BeneficiaryViewSet, basename='beneficiary')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'budgets', BudgetViewSet, basename='budget')

urlpatterns = [
    path('', include(router.urls)),
    path('transactions/create/', CreateTransactionAPIView.as_view(), name='transaction-create'),
    path('wallet/', WalletDetailView.as_view(), name='wallet-detail'),
    path('wallet/summary/', WalletSummaryView.as_view(), name='wallet-summary'),
    path('topup/', TopUpView.as_view(), name='topup'),
    path('withdraw/', WithdrawalView.as_view(), name='withdraw'),
    path('transfer/', TransferView.as_view(), name='transfer'),

]

