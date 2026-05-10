# payments/tests/test_views/test_audit_log_viewset.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from payments.models.audit_log import AuditAction, AuditLog

@pytest.mark.django_db
class TestAuditLogViewSet:

    @pytest.fixture
    def url(self):
        return reverse("payments:audit-log-list")

    def test_superuser_sees_all(self, api_client, superuser_factory, audit_log_factory, user_factory, url):
        superuser = superuser_factory()
        user2 = user_factory(is_active=True)
        log1 = audit_log_factory(user=superuser, action=AuditAction.LOGIN)
        log2 = audit_log_factory(user=user2, action=AuditAction.UPDATE)

        api_client.force_authenticate(user=superuser)
        resp = api_client.get(url)
        assert resp.status_code == 200
        ids = [x["id"] for x in resp.data["results"]]
        assert set(ids) == {log1.id, log2.id}

    def test_provider_sees_own_and_related(self, api_client, user_factory, institution_factory, business_factory, audit_log_factory, url):
        provider = user_factory(role="Provider", is_active=True)
        institution = institution_factory(owner=provider)
        business = business_factory(owner=provider)

        # logs
        log1 = audit_log_factory(user=provider, action=AuditAction.CREATE)           # binafsi
        log2 = audit_log_factory(target_obj=institution, action=AuditAction.UPDATE)   # institution
        log3 = audit_log_factory(target_obj=business, action=AuditAction.LOGIN)       # business
        log4 = audit_log_factory(user=user_factory(is_active=True), action=AuditAction.DELETE)  # mtu mwingine

        api_client.force_authenticate(provider)
        resp = api_client.get(url)
        assert resp.status_code == 200
        ids = [x["id"] for x in resp.data["results"]]
        # provider anaona logs zake + za biz/institution zake
        assert log1.id in ids
        assert log2.id in ids
        assert log3.id in ids
        # haona logs za wengine
        assert log4.id not in ids

    def test_normal_user_sees_only_own(self, api_client, user_factory, audit_log_factory, url):
        user = user_factory(role="CLIENT", is_active=True)
        log1 = audit_log_factory(user=user, action=AuditAction.LOGIN)
        # log ya mtu mwingine
        audit_log_factory(user=user_factory(is_active=True), action=AuditAction.UPDATE)

        api_client.force_authenticate(user)
        resp = api_client.get(url)
        assert resp.status_code == 200
        ids = [x["id"] for x in resp.data["results"]]
        assert ids == [log1.id]

    def test_anonymous_denied(self, api_client, audit_log_factory, user_factory, url):
        user = user_factory(is_active=True)
        audit_log_factory(user=user, action=AuditAction.LOGIN)

        resp = api_client.get(url)
        # DRF inarudisha 401 kwa unauthenticated user
        assert resp.status_code == 401