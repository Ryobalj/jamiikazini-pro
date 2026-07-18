# jamiichat/tests.py

import asyncio

import pytest
from channels.testing import WebsocketCommunicator
from django.urls import reverse
from rest_framework.test import APIClient

from jamiikazini.asgi import application
from jamiichat.models import Conversation, Message


@pytest.mark.django_db
def test_get_or_create_direct_is_idempotent(user_factory):
    a = user_factory()
    b = user_factory()

    convo1, created1 = Conversation.get_or_create_direct(a, b)
    convo2, created2 = Conversation.get_or_create_direct(b, a)  # order haijalishi

    assert created1 is True
    assert created2 is False
    assert convo1.id == convo2.id


@pytest.mark.django_db
def test_get_or_create_direct_separates_by_business(user_factory, business_factory):
    a = user_factory()
    b = user_factory()
    business = business_factory(owner=b)

    general, _ = Conversation.get_or_create_direct(a, b)
    business_convo, _ = Conversation.get_or_create_direct(a, b, business=business)

    assert general.id != business_convo.id
    assert business_convo.business_id == business.id


@pytest.mark.django_db
def test_start_with_user_creates_conversation_and_message(user_factory):
    a = user_factory()
    b = user_factory(email='targetuser@example.com')

    client = APIClient()
    client.force_authenticate(user=a)

    response = client.post(
        reverse('jamiichat:conversation-start-with-user'),
        {'user_identifier': 'targetuser@example.com', 'message': 'Habari, unauza nini?'},
        format='json',
    )

    assert response.status_code == 201, response.content
    data = response.json()
    assert data['last_message']['content'] == 'Habari, unauza nini?'
    assert data['other_participant']['email'] == 'targetuser@example.com'

    convo = Conversation.objects.get(id=data['id'])
    assert convo.participants.filter(id=a.id).exists()
    assert convo.participants.filter(id=b.id).exists()


@pytest.mark.django_db
def test_start_with_business_targets_owner(user_factory, business_factory):
    customer = user_factory()
    owner = user_factory()
    business = business_factory(owner=owner)

    client = APIClient()
    client.force_authenticate(user=customer)

    response = client.post(
        reverse('jamiichat:conversation-start-with-business'),
        {'business_id': str(business.id), 'message': 'Mnauza saa ngapi mpaka lini?'},
        format='json',
    )

    assert response.status_code == 201, response.content
    data = response.json()
    assert data['business'] == str(business.id)
    assert str(data['other_participant']['id']) == str(owner.id)


@pytest.mark.django_db
def test_cannot_start_business_conversation_with_own_business(user_factory, business_factory):
    owner = user_factory()
    business = business_factory(owner=owner)

    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        reverse('jamiichat:conversation-start-with-business'),
        {'business_id': str(business.id), 'message': 'jaribio'},
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_conversation_list_scoped_to_participants(user_factory):
    a = user_factory()
    b = user_factory()
    stranger = user_factory()
    convo, _ = Conversation.get_or_create_direct(a, b)
    Message.objects.create(conversation=convo, sender=a, content='hujambo')

    client = APIClient()
    client.force_authenticate(user=stranger)
    response = client.get(reverse('jamiichat:conversation-list'))

    body = response.json()
    results = body.get('results', body) if isinstance(body, dict) else body
    assert len(results) == 0

    client.force_authenticate(user=a)
    response = client.get(reverse('jamiichat:conversation-list'))
    body = response.json()
    results = body.get('results', body) if isinstance(body, dict) else body
    assert len(results) == 1


@pytest.mark.django_db
def test_mark_read_only_marks_others_messages(user_factory):
    a = user_factory()
    b = user_factory()
    convo, _ = Conversation.get_or_create_direct(a, b)
    Message.objects.create(conversation=convo, sender=a, content='kutoka a')
    Message.objects.create(conversation=convo, sender=b, content='kutoka b')

    client = APIClient()
    client.force_authenticate(user=a)
    response = client.post(reverse('jamiichat:conversation-mark-read', args=[convo.id]))

    assert response.status_code == 200
    assert response.json()['marked_read'] == 1  # ujumbe wa a hauwekwi 'read' na yeye mwenyewe
    assert Message.objects.get(sender=b).is_read is True
    assert Message.objects.get(sender=a).is_read is False


@pytest.mark.django_db(transaction=True)
def test_websocket_delivers_message_between_participants(user_factory):
    a = user_factory()
    b = user_factory()
    convo, _ = Conversation.get_or_create_direct(a, b)

    from rest_framework_simplejwt.tokens import RefreshToken
    token_a = str(RefreshToken.for_user(a).access_token)
    token_b = str(RefreshToken.for_user(b).access_token)

    async def scenario():
        comm_a = WebsocketCommunicator(application, f"/ws/chat/{convo.id}/?token={token_a}")
        comm_b = WebsocketCommunicator(application, f"/ws/chat/{convo.id}/?token={token_b}")

        connected_a, _ = await comm_a.connect()
        connected_b, _ = await comm_b.connect()
        assert connected_a is True
        assert connected_b is True

        await comm_a.send_json_to({"content": "Habari mwenzangu"})

        received_by_b = await comm_b.receive_json_from(timeout=5)
        assert received_by_b["content"] == "Habari mwenzangu"
        assert received_by_b["sender"] == a.id

        await comm_a.disconnect()
        await comm_b.disconnect()

    asyncio.run(scenario())

    assert Message.objects.filter(conversation=convo, content="Habari mwenzangu").exists()
