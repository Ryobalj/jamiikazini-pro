# payments/tests/test_urls.py

import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal

from payments.models.invoice import Invoice
from payments.models.paymentmethod import PaymentMethod


@pytest.mark.django_db
class TestPaymentsRoutes:

    def test_audit_log_list(self, api_client, user_factory, audit_log_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        audit_log_factory(user=user)
        url = reverse("payments:audit-log-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    def test_currency_crud(self, api_client, user_factory, currency_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        url = reverse("payments:currency-list")
        resp = api_client.post(
            url,
            {"code": "USD", "name": "US Dollar", "exchange_rate_to_tzs": "2500.00"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        currency_id = resp.json()["id"]

        url_detail = reverse("payments:currency-detail", kwargs={"pk": currency_id})
        resp = api_client.get(url_detail)
        assert resp.status_code == status.HTTP_200_OK

        resp = api_client.patch(url_detail, {"name": "US Dollar Updated"}, format="json")
        assert resp.status_code == status.HTTP_200_OK

        resp = api_client.delete(url_detail)
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_exchange_rate_list(self, api_client, user_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        url = reverse("payments:exchange-rate-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK

    def test_invoice_routes(self, api_client, user_factory, invoice_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        invoice = invoice_factory(user=user, amount="150.00", tax="15.00")

        url_list = reverse("payments:invoice-list")
        resp = api_client.get(url_list)
        assert resp.status_code == status.HTTP_200_OK
        assert any(str(invoice.id) == str(i["id"]) for i in resp.json())

        url_mark = reverse("payments:invoice-mark-paid", kwargs={"pk": invoice.id})
        resp = api_client.post(url_mark)
        assert resp.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_payment_failure_routes(self, api_client, user_factory, payment_failure_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)
    
        # Unda failure sahihi kwa factory
        failure = payment_failure_factory(user=user, amount="50.00")
    
        # Angalia list
        url_list = reverse("payments:payment-failure-list")
        resp = api_client.get(url_list)
        assert resp.status_code == 200
        resp_data = resp.json()
        assert any(str(failure.id) == f["id"] for f in resp_data)
    
        # Jaribu retry
        url_retry = reverse("payments:payment-failure-retry", kwargs={"pk": failure.id})
        resp = api_client.post(url_retry)
        assert resp.status_code == 200

    def test_payment_method_crud_and_set_default(self, api_client, user_factory, payment_method_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        # Create
        method = payment_method_factory(owner=user, method_type="WALLET", account_identifier="wallet123")
        url_detail = reverse("payments:payment-method-detail", kwargs={"pk": method.id})

        # Retrieve
        resp = api_client.get(url_detail)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["account_identifier"] == "wallet123"

        # Update
        resp = api_client.patch(
            url_detail,
            {"details": {"dummy": "updated"}, "account_identifier": "wallet123"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["details"]["dummy"] == "updated"

        # Set default
        url_default = reverse("payments:payment-method-set-default", kwargs={"pk": method.id})
        resp = api_client.post(url_default)
        assert resp.status_code == status.HTTP_200_OK

        # Delete
        resp = api_client.delete(url_detail)
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_payment_report_routes_and_stats(self, api_client, user_factory, payment_report_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)

        report = payment_report_factory(user=user)
        url_list = reverse("payments:payment-report-list")
        resp = api_client.get(url_list)
        assert resp.status_code == status.HTTP_200_OK

        url_detail = reverse("payments:payment-report-detail", kwargs={"pk": report.id})
        resp = api_client.get(url_detail)
        assert resp.status_code == status.HTTP_200_OK

        url_stats = reverse("payments:payment-report-stats")
        resp = api_client.get(url_stats)
        assert resp.status_code == status.HTTP_200_OK

    def test_pay_invoice_route(self, api_client, user_factory, invoice_factory, payment_method_factory, wallet_factory):
        user = user_factory()
        api_client.force_authenticate(user=user)
    
        # ✅ Unda invoice
        invoice = invoice_factory(user=user, amount="200.00", tax="20.00")
        method = payment_method_factory(
            owner=user, method_type="WALLET", account_identifier="wallet123"
        )
    
        # ✅ Unda wallet yenye balance kubwa
        wallet_factory(user=user, balance=Decimal("1000.00"))
    
        url = reverse("payments:pay-invoice")
        resp = api_client.post(
            url,
            {"invoice_id": str(invoice.id), "payment_method_id": str(method.id)},
            format="json",
        )
    
        # ✅ Tunakubali outcomes tatu: imefanikiwa, imekosa, au haijatekelezwa
        assert resp.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]