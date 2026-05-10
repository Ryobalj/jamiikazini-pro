# payments/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments.views.webhook_api import PaymentWebhookView

from payments.views import (
    audit_log_views,
    currency_views,
    exchange_rate_views,
    invoice_views,
    payment_failure_views,
    payment_method_views,
    payment_method_api,
    payment_report_views,
)

router = DefaultRouter()

# CRUD / Read-only viewsets
router.register(r"audit-logs", audit_log_views.AuditLogViewSet, basename="audit-log")
router.register(r"currencies", currency_views.CurrencyViewSet, basename="currency")
router.register(r"exchange-rates", exchange_rate_views.ExchangeRateViewSet, basename="exchange-rate")
router.register(r"invoices", invoice_views.InvoiceViewSet, basename="invoice")
router.register(r"payment-failures", payment_failure_views.PaymentFailureViewSet, basename="payment-failure")
router.register(r"payment-methods", payment_method_views.PaymentMethodViewSet, basename="payment-method")  # <-- hii sasa CRUD sahihi
router.register(r"payment-reports", payment_report_views.PaymentReportViewSet, basename="payment-report")

# Wallet / payment endpoint
pay_invoice = payment_method_api.PaymentViewSet.as_view({
    'post': 'pay_invoice'
})

app_name = "payments"

urlpatterns = [
    path("", include(router.urls)),
    path("pay-invoice/", pay_invoice, name="pay-invoice"),
    path("webhooks/<str:gateway>/", PaymentWebhookView.as_view(), name="payments-webhook"),

]
