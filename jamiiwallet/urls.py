# jamiiwallet/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from jamiiwallet.views.transaction_views import TransactionViewSet, CreateTransactionAPIView
from jamiiwallet.views.wallet_views import WalletDetailView
from jamiiwallet.views.topup_views import TopUpView
from jamiiwallet.views.withdrawal_views import WithdrawalView

app_name = 'wallet'

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('transactions/create/', CreateTransactionAPIView.as_view(), name='transaction-create'),
    path('wallet/', WalletDetailView.as_view(), name='wallet-detail'),
    path('topup/', TopUpView.as_view(), name='topup'),
    path('withdraw/', WithdrawalView.as_view(), name='withdraw'),

]

