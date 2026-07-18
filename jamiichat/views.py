# jamiichat/views.py

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from businesses.models.business import Business
from jamiiwallet.serializers.transfer_serializer import find_recipient
from jamiichat.models import Conversation, Message
from jamiichat.serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Orodha ya mazungumzo ya mtumiaji (inbox). Kuanzisha mazungumzo mapya
    hufanyika kupitia start-with-user/start-with-business (si create ya
    kawaida - inahitaji ujumbe wa kwanza + azimio la mwenzake).
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related(
            'participants', 'business'
        )

    def _start(self, request, other_user, business=None):
        message_text = (request.data.get('message') or '').strip()
        if not message_text:
            raise ValidationError({'message': 'Andika ujumbe wa kwanza.'})

        conversation, _created = Conversation.get_or_create_direct(request.user, other_user, business=business)
        Message.objects.create(conversation=conversation, sender=request.user, content=message_text)
        conversation.save()  # gusa updated_at

        serializer = self.get_serializer(conversation, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='start-with-user')
    def start_with_user(self, request):
        identifier = request.data.get('user_identifier')
        other_user = find_recipient(identifier)
        if not other_user:
            raise ValidationError({'user_identifier': 'Mtumiaji hakupatikana.'})
        if other_user.id == request.user.id:
            raise ValidationError({'user_identifier': 'Huwezi kuanzisha mazungumzo na wewe mwenyewe.'})
        return self._start(request, other_user)

    @action(detail=False, methods=['post'], url_path='start-with-business')
    def start_with_business(self, request):
        business_id = request.data.get('business_id')
        business = get_object_or_404(Business, pk=business_id)
        if not business.owner:
            raise ValidationError({'business_id': 'Biashara hii haina mmiliki wa kuwasiliana naye.'})
        if business.owner_id == request.user.id:
            raise ValidationError({'business_id': 'Hii ni biashara yako mwenyewe.'})
        return self._start(request, business.owner, business=business)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        qs = conversation.messages.select_related('sender').order_by('created_at')
        return Response(MessageSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        conversation = self.get_object()
        updated = conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        return Response({'marked_read': updated})
