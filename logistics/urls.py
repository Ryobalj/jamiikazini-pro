# logistics/urls.py

from django.urls import path, include

urlpatterns = [
    path('transport/', include('logistics.urls.transport_urls')),

]