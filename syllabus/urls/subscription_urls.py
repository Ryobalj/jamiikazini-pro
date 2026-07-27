# syllabus/urls/subscription_urls.py

from django.urls import path
from syllabus.views.subscription_views import SubscriptionStatusAPIView

urlpatterns = [
    path("subscription/", SubscriptionStatusAPIView.as_view(), name="syllabus-subscription-status"),
]
