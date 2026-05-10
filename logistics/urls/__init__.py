# logistics/urls/__init__.py

from django.urls import path, include

urlpatterns = [
    path('', include('logistics.urls.driver_urls')),
    path('', include('logistics.urls.shipment_urls')),
    path('', include('logistics.urls.transport_assignment_urls')),
    path('', include('logistics.urls.transport_leg_urls')),
    path('', include('logistics.urls.transport_provider_verification_urls')),
    path('', include('logistics.urls.transport_request_urls')),
    path('', include('logistics.urls.transport_urls')),
    path('', include('logistics.urls.vehicle_urls')),
  
]