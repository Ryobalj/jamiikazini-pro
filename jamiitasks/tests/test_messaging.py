import pytest

# jamiichat is still docs-only: the Message model these tests exercise does not
# exist yet. Un-skip when jamiichat models land (see jamiichat/README.md).
pytest.skip(
    "jamiichat.Message model not implemented yet (jamiichat app is docs-only)",
    allow_module_level=True,
)

from django.contrib.auth import get_user_model
from jamiichat.models import Message
from jamiitasks.services import messaging_gateway as mg

pytestmark = pytest.mark.django_db
User = get_user_model()

@pytest.fixture
def sender():
    return User.objects.create_user(username="sender", password="pass123")

@pytest.fixture
def recipient():
    return User.objects.create_user(username="recipient", password="pass123")

def test_send_message_success(sender, recipient):
    result = mg.send_chat_message(sender.id, recipient.id, "Hello there!")

    message = Message.objects.get(id=result["message_id"])

    assert message.content == "Hello there!"
    assert message.sender == sender
    assert message.recipient == recipient
    assert message.status == "sent"
    assert result["status"] == "success"

def test_send_message_invalid_sender(recipient):
    with pytest.raises(User.DoesNotExist):
        mg.send_chat_message(sender_id=9999, recipient_id=recipient.id, message_text="Hello")

def test_send_message_invalid_recipient(sender):
    with pytest.raises(User.DoesNotExist):
        mg.send_chat_message(sender_id=sender.id, recipient_id=8888, message_text="Hello")

def test_send_message_retry_on_exception(mocker, sender, recipient):
    # Simulate first call raises error, second succeeds
    Message = mocker.patch("jamiitasks.services.messaging_gateway.apps.get_model")
    fake_model = mocker.Mock()
    fake_model.objects.create.side_effect = [Exception("DB Error"), mocker.Mock(id=123, sent_at="2023-01-01T00:00:00Z")]
    Message.return_value = fake_model

    mock_user = mocker.patch("jamiitasks.services.messaging_gateway.User.objects.get")
    mock_user.side_effect = lambda id: sender if id == sender.id else recipient

    result = mg.send_chat_message(sender.id, recipient.id, "Retrying...")
    assert result["status"] == "success"