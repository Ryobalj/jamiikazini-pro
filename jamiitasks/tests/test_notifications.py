import pytest
from unittest.mock import patch
from jamiitasks.tasks import notifications

pytestmark = pytest.mark.django_db

def test_send_sms_task_success(mocker):
    mock_send = mocker.patch("jamiitasks.services.sms_gateway.send_sms", return_value=True)
    result = notifications.send_sms_task.run(phone="+255700000001", message="Hello from Jamiikazini")
    mock_send.assert_called_once_with("+255700000001", "Hello from Jamiikazini")
    assert result is True

def test_send_sms_task_retry_on_failure(mocker):
    mock_send = mocker.patch("jamiitasks.services.sms_gateway.send_sms", side_effect=Exception("SMS error"))
    mock_retry = mocker.patch.object(notifications.send_sms_task, "retry", side_effect=Exception("Retry triggered"))
    
    with pytest.raises(Exception) as exc_info:
        notifications.send_sms_task.run(phone="+255700000001", message="Failed SMS")
    
    assert "Retry triggered" in str(exc_info.value)
    mock_send.assert_called_once()

def test_send_email_task_success(mocker):
    mock_send = mocker.patch("jamiitasks.services.email_gateway.send_email", return_value=True)
    result = notifications.send_email_task.run(to_email="test@example.com", subject="Subject", body="Body")
    mock_send.assert_called_once_with("test@example.com", "Subject", "Body")
    assert result is True

def test_send_email_task_retry_on_failure(mocker):
    mock_send = mocker.patch("jamiitasks.services.email_gateway.send_email", side_effect=Exception("Email fail"))
    mock_retry = mocker.patch.object(notifications.send_email_task, "retry", side_effect=Exception("Retrying Email"))

    with pytest.raises(Exception) as exc_info:
        notifications.send_email_task.run(to_email="fail@example.com", subject="Oops", body="Failed body")

    assert "Retrying Email" in str(exc_info.value)
    mock_send.assert_called_once()

def test_send_push_notification_task_success(mocker):
    mock_send = mocker.patch("jamiitasks.services.push_gateway.send_push", return_value=True)
    result = notifications.send_push_notification_task.run(user_id=123, message="You've got a push")
    mock_send.assert_called_once_with(123, "You've got a push")
    assert result is True

def test_send_push_notification_task_retry_on_failure(mocker):
    mock_send = mocker.patch("jamiitasks.services.push_gateway.send_push", side_effect=Exception("Push error"))
    mock_retry = mocker.patch.object(notifications.send_push_notification_task, "retry", side_effect=Exception("Push retry triggered"))

    with pytest.raises(Exception) as exc_info:
        notifications.send_push_notification_task.run(user_id=456, message="Will fail")

    assert "Push retry triggered" in str(exc_info.value)
    mock_send.assert_called_once()