# realestate/urls.py

from rest_framework.routers import DefaultRouter

from realestate.views.property_views import PropertyListingViewSet
from realestate.views.property_inquiry_views import PropertyInquiryViewSet

router = DefaultRouter()
router.register(r"properties", PropertyListingViewSet, basename="property-listing")
router.register(r"inquiries", PropertyInquiryViewSet, basename="property-inquiry")

urlpatterns = router.urls
