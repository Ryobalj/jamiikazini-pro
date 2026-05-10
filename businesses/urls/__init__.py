# businesses/urls/__init__.py

from django.urls import path, include

app_name = "businesses"

urlpatterns = [
    # Nested business-related routes (businesses,branches, products, services, reviews, bookings)
    path('', include('businesses.urls.nested_business_urls')),

]