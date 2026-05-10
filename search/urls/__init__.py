# search/urls/__init__.py

from django.urls import path, include

urlpatterns = [
    path('', include('search.urls.branch_search_urls')),
    path('', include('search.urls.review_search_urls')),
    path('', include('search.urls.business_search_urls')),
    path('', include('search.urls.department_search_urls')),
    path('', include('search.urls.product_search_urls')),
    path('', include('search.urls.service_search_urls')),
    path('', include('search.urls.transport_provider_search_urls')),
    path('', include('search.urls.transport_leg_search_urls')),
    path('', include('search.urls.driver_search_urls')),
    path('', include('search.urls.shipment_search_urls')),
    path('', include('search.urls.staff_profile_search_urls')),
    path('', include('search.urls.transport_provider_verification_search_urls')),
    path("", include("search.urls.syllabus_search_urls")),


]
