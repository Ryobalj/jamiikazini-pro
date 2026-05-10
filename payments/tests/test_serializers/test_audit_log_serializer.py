# payments/tests/test_serializers/test_audit_log_serializer.py

import pytest
import uuid
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from payments.models.audit_log import AuditLog, AuditAction
from payments.serializers.audit_log_serializer import (
    AuditLogSerializer,
    AuditLogCreateSerializer,
)


@pytest.fixture
def audit_log(db, user_factory):
    user = user_factory(full_name="John Doe")
    ct = ContentType.objects.get_for_model(user)
    log = AuditLog.objects.create(
        user=user,
        action=AuditAction.CREATE,
        content_type=ct,
        object_id=user.pk,
        description="Created user",
        metadata={"foo": "bar"},
        ip_address="127.0.0.1",
    )
    return log


def test_audit_log_serializer_basic_fields(audit_log):
    serializer = AuditLogSerializer(audit_log)
    data = serializer.data

    assert data["id"] == audit_log.id
    assert data["user"] == audit_log.user.id
    assert data["user_name"] == audit_log.user.full_name
    assert data["action"] == audit_log.action
    assert data["action_display"] == audit_log.get_action_display()
    assert data["content_type"] == audit_log.content_type.id
    assert data["content_type_name"] == "User"
    assert data["object_id"] == str(audit_log.object_id)
    assert data["description"] == "Created user"
    assert data["metadata"] == {"foo": "bar"}
    assert data["ip_address"] == "127.0.0.1"


def test_audit_log_serializer_user_name_fallback(user_factory):
    user = user_factory(full_name="")  # empty full_name triggers fallback
    ct = ContentType.objects.get_for_model(user)
    log = AuditLog.objects.create(
        user=user,
        action=AuditAction.UPDATE,
        content_type=ct,
        object_id=user.pk,
        description="Updated user",
    )
    serializer = AuditLogSerializer(log)
    data = serializer.data
    assert data["user_name"] == str(user)


def test_audit_log_serializer_user_none(db):
    from accounts.models import User  # needed for ContentType
    ct = ContentType.objects.get_for_model(User)
    log = AuditLog.objects.create(
        user=None,
        action=AuditAction.DELETE,
        content_type=ct,
        object_id=uuid.uuid4(),
        description="System deleted object",
    )
    serializer = AuditLogSerializer(log)
    data = serializer.data
    assert data["user_name"] == "System"


def test_audit_log_serializer_with_expand(user_factory):
    user = user_factory(full_name="Jane Doe")
    ct = ContentType.objects.get_for_model(user)
    log = AuditLog.objects.create(
        user=user,
        action=AuditAction.CREATE,
        content_type=ct,
        object_id=user.pk,
    )

    factory = APIRequestFactory()
    request = factory.get("/?expand=target_object")
    drf_request = Request(request)

    serializer = AuditLogSerializer(log, context={"request": drf_request})
    data = serializer.data
    assert "id" in data["target_object_data"]  # should include user fields
    assert data["target_object_data"]["id"] == user.id


def test_audit_log_serializer_expand_no_target_object(user_factory):
    user = user_factory()
    ct = ContentType.objects.get_for_model(user)
    log = AuditLog.objects.create(
        user=user,
        action=AuditAction.CREATE,
        content_type=ct,
        object_id=uuid.uuid4(),  # non-existing target
    )

    factory = APIRequestFactory()
    request = factory.get("/?expand=target_object")
    drf_request = Request(request)

    serializer = AuditLogSerializer(log, context={"request": drf_request})
    data = serializer.data
    assert data["target_object_data"] is None


def test_audit_log_create_serializer_valid(user_factory):
    user = user_factory()
    ct = ContentType.objects.get_for_model(user)
    payload = {
        "user": user.id,
        "action": AuditAction.CREATE,
        "content_type": ct.id,
        "object_id": user.pk,
        "description": "User created",
        "metadata": {"a": 1},
        "ip_address": "10.0.0.1",
    }
    serializer = AuditLogCreateSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    log = serializer.save()
    assert isinstance(log, AuditLog)
    assert log.metadata == {"a": 1}


def test_audit_log_create_serializer_invalid_action(user_factory):
    user = user_factory()
    ct = ContentType.objects.get_for_model(user)
    payload = {
        "user": user.id,
        "action": "NOT_REAL",
        "content_type": ct.id,
        "object_id": user.pk,
        "description": "Bad action",
    }
    serializer = AuditLogCreateSerializer(data=payload)
    assert not serializer.is_valid()
    assert "action" in serializer.errors


def test_audit_log_create_serializer_defaults_metadata(user_factory):
    user = user_factory()
    ct = ContentType.objects.get_for_model(user)
    payload = {
        "user": user.id,
        "action": AuditAction.UPDATE,
        "content_type": ct.id,
        "object_id": user.pk,
        "description": "No metadata passed",
    }
    serializer = AuditLogCreateSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    log = serializer.save()
    assert log.metadata == {}  # default set in create()