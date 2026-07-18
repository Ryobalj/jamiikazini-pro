from django.contrib import admin

from jamiichat.models import Conversation, Message

admin.site.register(Conversation)
admin.site.register(Message)
