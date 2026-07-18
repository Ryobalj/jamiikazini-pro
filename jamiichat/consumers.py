# jamiichat/consumers.py

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from jamiichat.models import Conversation, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        if not await self._is_participant(user):
            await self.close(code=4003)
            return

        self.group_name = f'chat_{self.conversation_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        text = (content.get('content') or '').strip()
        if not text:
            return

        user = self.scope['user']
        message = await self._save_message(user, text)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.message',
                'message': {
                    'id': str(message.id),
                    'conversation': str(message.conversation_id),
                    'sender': user.id,
                    'sender_name': user.full_name or user.email,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                },
            },
        )

    async def chat_message(self, event):
        await self.send_json(event['message'])

    @database_sync_to_async
    def _is_participant(self, user):
        return Conversation.objects.filter(id=self.conversation_id, participants=user).exists()

    @database_sync_to_async
    def _save_message(self, user, text):
        from kiini.helpers.notification_helper import notify_user
        from kiini.models.notification import NotificationType

        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(conversation=conversation, sender=user, content=text)
        conversation.save()  # gusa updated_at (auto_now) ili mazungumzo mapya yaonekane juu

        recipient = conversation.other_participant(user)
        if recipient:
            notify_user(
                recipient,
                f"Ujumbe mpya kutoka kwa {user.full_name or user.email}: {text[:80]}",
                notification_type=NotificationType.CHAT,
                link=f"/jamiichat/{conversation.id}",
            )

        return message
