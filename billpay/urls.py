# billpay/urls.py

from rest_framework.routers import DefaultRouter

from billpay.views.bill_payment_views import BillerViewSet, BillPaymentViewSet

router = DefaultRouter()
router.register(r"billers", BillerViewSet, basename="biller")
router.register(r"payments", BillPaymentViewSet, basename="bill-payment")

urlpatterns = router.urls
