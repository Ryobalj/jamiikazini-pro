# jamiichat/serializers.py

from rest_framework import serializers

from accounts.serializers import UserMinimalSerializer
from jamiichat.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'created_at', 'is_read']
        read_only_fields = ['id', 'conversation', 'sender', 'sender_name', 'created_at', 'is_read']


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserMinimalSerializer(many=True, read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    last_message = MessageSerializer(read_only=True)
    other_participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'other_participant', 'business', 'business_name',
            'last_message', 'unread_count', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_other_participant(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        other = obj.other_participant(user) if user else None
        return UserMinimalSerializer(other).data if other else None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=user).count()
