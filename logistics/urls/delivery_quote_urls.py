# logistics/urls/delivery_quote_urls.py

from django.urls import path
from logistics.views.delivery_quote_views import DeliveryQuoteView

urlpatterns = [
    path('delivery-quote/', DeliveryQuoteView.as_view(), name='delivery-quote'),
]
