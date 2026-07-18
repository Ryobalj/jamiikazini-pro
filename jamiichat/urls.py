# jamiichat/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from jamiichat.views import ConversationViewSet

app_name = 'jamiichat'

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
]
