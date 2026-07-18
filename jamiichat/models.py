# jamiichat/models.py

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class Conversation(models.Model):
    """
    Mazungumzo kati ya watumiaji wawili. Kama yalianzishwa kutoka homepage/
    storefront ya biashara fulani (mfano 'Wasiliana na Muuzaji'), 'business'
    inahifadhi hilo - inasaidia mmiliki wa biashara kuona maswali ya wateja
    kwa urahisi (engagement), tofauti na mazungumzo ya kawaida ya kirafiki.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text=_('Biashara husika, ikiwa mazungumzo yalianzishwa kutoka homepage yake'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')

    def __str__(self):
        names = ', '.join(u.full_name or u.email for u in self.participants.all()[:3])
        return f'Conversation({names})'

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    @classmethod
    def get_or_create_direct(cls, user_a, user_b, business=None):
        """
        Pata (au tengeneza) mazungumzo ya moja kwa moja kati ya watu wawili.
        'business' ikitofautiana, mazungumzo mapya yanaundwa (mfano mtu
        anaweza kuwa na mazungumzo ya kawaida NA mazungumzo ya biashara
        maalum na mtu yule yule).
        """
        if user_a.id == user_b.id:
            raise ValueError('Huwezi kuanzisha mazungumzo na wewe mwenyewe.')

        qs = cls.objects.filter(participants=user_a).filter(participants=user_b)
        qs = qs.filter(business=business) if business else qs.filter(business__isnull=True)
        # NB: si .annotate(Count('participants')) hapa - kuchain .filter()
        # mbili kwenye M2M moja kunatengeneza join mbili tofauti, na
        # kuziunganisha na annotate(Count(...)) kunazidisha idadi ya rows
        # (join multiplication) - pcount huwa si sahihi. Candidates ni chache
        # sana kwa vitendo, hivyo tunahesabu kwa Python badala ya SQL.
        for candidate in qs.distinct():
            if candidate.participants.count() == 2:
                return candidate, False

        convo = cls.objects.create(business=business)
        convo.participants.add(user_a, user_b)
        return convo, True


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f'{self.sender}: {self.content[:50]}'
