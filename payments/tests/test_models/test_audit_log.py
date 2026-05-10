# payments/tests/test_models/test_audit_log.py

import uuid
import pytest
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from payments.models.audit_log import AuditLog, AuditAction
from django.utils.translation import gettext_lazy as _


@pytest.mark.django_db
def test_str_with_full_name(user_factory):
    user = user_factory(full_name="Test User")
    log = AuditLog.objects.create(
        user=user,
        action=AuditAction.CREATE,
        description="Created something"
    )
    expected = _("{action} on {target} by {user}").format(
        action=log.get_action_display(),
        target=_("N/A"),
        user="Test User"
    )
    assert str(log) == expected


@pytest.mark.django_db
def test_str_with_system_user_none():
    log = AuditLog.objects.create(
        user=None,
        action=AuditAction.DELETE
    )
    expected = _("{action} on {target} by {user}").format(
        action=log.get_action_display(),
        target=_("N/A"),
        user=_("System")
    )
    assert str(log) == expected


@pytest.mark.django_db
def test_str_with_content_type_and_object_id(user_factory):
    user = user_factory(full_name="Another User")
    obj_uuid = uuid.uuid4()
    content_type = ContentType.objects.get_for_model(user)
    log = AuditLog.objects.create(
        user=user,
        action=AuditAction.UPDATE,
        content_type=content_type,
        object_id=obj_uuid
    )
    expected_target = f"{content_type} ({obj_uuid})"
    expected = _("{action} on {target} by {user}").format(
        action=log.get_action_display(),
        target=expected_target,
        user="Another User"
    )
    assert str(log) == expected


@pytest.mark.django_db
def test_str_with_content_type_but_no_user(user_factory):
    obj_uuid = uuid.uuid4()
    content_type = ContentType.objects.get_for_model(user_factory())
    log = AuditLog.objects.create(
        user=None,
        action=AuditAction.UPDATE,
        content_type=content_type,
        object_id=obj_uuid
    )
    expected_target = f"{content_type} ({obj_uuid})"
    expected = _("{action} on {target} by {user}").format(
        action=log.get_action_display(),
        target=expected_target,
        user=_("System")
    )
    assert str(log) == expected


@pytest.mark.django_db
def test_clean_with_invalid_uuid(user_factory):
    user = user_factory()
    log = AuditLog(
        user=user,
        action=AuditAction.OTHER,
        object_id="invalid-uuid"
    )
    with pytest.raises(ValidationError) as exc:
        log.clean()
    assert "Invalid UUID format" in str(exc.value)


@pytest.mark.django_db
def test_save_calls_clean(mocker, user_factory):
    user = user_factory()
    log = AuditLog(user=user, action=AuditAction.LOGIN)
    mock_clean = mocker.patch.object(AuditLog, "full_clean")
    log.save()
    mock_clean.assert_called_once()


@pytest.mark.django_db
def test_log_action_without_target(user_factory):
    user = user_factory()
    log = AuditLog.log_action(user=user, action=AuditAction.LOGOUT)
    assert log.content_type is None
    assert log.object_id is None


@pytest.mark.django_db
def test_log_action_defaults(user_factory):
    user = user_factory()
    log = AuditLog.log_action(user=user, action=AuditAction.OTHER)
    assert log.description == ""
    assert log.metadata == {}


@pytest.mark.django_db
def test_log_action_with_uuid_target(user_factory):
    user = user_factory()
    target = user_factory()  # Django model instance yenye _meta
    target.pk = uuid.uuid4()  # Badilisha PK kuwa UUID

    log = AuditLog.log_action(
        user=user,
        action=AuditAction.CREATE,
        target_obj=target,
        description="Something happened",
        metadata={"key": "value"},
        ip_address="127.0.0.1"
    )
    assert isinstance(log, AuditLog)
    assert log.user == user
    assert log.action == AuditAction.CREATE
    assert log.object_id == target.pk
    assert log.metadata == {"key": "value"}
    assert log.ip_address == "127.0.0.1"


@pytest.mark.django_db
def test_log_action_with_non_uuid_pk(user_factory):
    user = user_factory()
    target = user_factory()
    target.pk = uuid.UUID("00000000-0000-0000-0000-000000000123")  # Valid UUID object

    log = AuditLog.log_action(
        user=user,
        action=AuditAction.PAYMENT,
        target_obj=target
    )
    assert isinstance(log.object_id, uuid.UUID)
    assert log.action == AuditAction.PAYMENT
