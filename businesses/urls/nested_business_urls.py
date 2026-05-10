# businesses/urls/nested_business_urls.py

from django.urls import path
from rest_framework_nested import routers

from businesses.views.business_views import BusinessViewSet
from businesses.views.branch_views import BranchViewSet
from businesses.views.product_views import (
    ProductViewSet,
    ProductListByProximityView,
    generate_product_url
)
from businesses.views.service_views import ServiceViewSet
from businesses.views.review_views import ProductReviewViewSet, ServiceReviewViewSet
from businesses.views.product_order_views import ProductOrderViewSet
from businesses.views.service_booking_views import ServiceBookingViewSet
from businesses.views.booking_views import BookingViewSet, BookingLogViewSet
from businesses.views.category_views import BusinessCategoryViewSet
from businesses.views.utils import check_domain_availability
from businesses.views.public_views import PublicBusinessDetailView
from businesses.views.nearby_views import NearbyEntitiesView


# =========================
# Primary: /api/v1/businesses/
# =========================

router = routers.DefaultRouter()
router.register(r"businesses", BusinessViewSet, basename="businesses")
router.register(r"categories", BusinessCategoryViewSet, basename="business-categories")


# ================================
# Nested: branches under business
# ================================

branch_router = routers.NestedDefaultRouter(router, r"businesses", lookup="business")
branch_router.register(r"branches", BranchViewSet, basename="business-branches")


# =================================
# Nested: products under business
# =================================

business_product_router = routers.NestedDefaultRouter(router, r"businesses", lookup="business")
business_product_router.register(r"products", ProductViewSet, basename="business-products")

product_order_router = routers.NestedDefaultRouter(business_product_router, r"products", lookup="product")
product_order_router.register(r"orders", ProductOrderViewSet, basename="product-orders")

product_review_router = routers.NestedDefaultRouter(business_product_router, r"products", lookup="product")
product_review_router.register(r"reviews", ProductReviewViewSet, basename="product-reviews")


# ===============================
# Nested: services under business
# ===============================

business_service_router = routers.NestedDefaultRouter(router, r"businesses", lookup="business")
business_service_router.register(r"services", ServiceViewSet, basename="business-services")


# =========================================
# Nested: services under branch
# =========================================

branch_service_router = routers.NestedDefaultRouter(branch_router, r"branches", lookup="branch")
branch_service_router.register(r"services", ServiceViewSet, basename="branch-services")

branch_service_booking_router = routers.NestedDefaultRouter(branch_service_router, r"services", lookup="service")
branch_service_booking_router.register(r"bookings", ServiceBookingViewSet, basename="service-bookings")

branch_service_review_router = routers.NestedDefaultRouter(branch_service_router, r"services", lookup="service")
branch_service_review_router.register(r"reviews", ServiceReviewViewSet, basename="service-reviews")

booking_log_router = routers.NestedDefaultRouter(branch_service_booking_router, r"bookings", lookup="booking")
booking_log_router.register(r"logs", BookingLogViewSet, basename="booking-logs")


# ========================================
# Nested: products under branch
# ========================================

branch_product_router = routers.NestedDefaultRouter(branch_router, r"branches", lookup="branch")
branch_product_router.register(r"products", ProductViewSet, basename="branch-products")

branch_product_order_router = routers.NestedDefaultRouter(branch_product_router, r"products", lookup="product")
branch_product_order_router.register(r"orders", ProductOrderViewSet, basename="branch-product-orders")

branch_product_review_router = routers.NestedDefaultRouter(branch_product_router, r"products", lookup="product")
branch_product_review_router.register(r"reviews", ProductReviewViewSet, basename="branch-product-reviews")

# ============================
# Router-based URL patterns
# ============================

router_urlpatterns = (
    router.urls +
    branch_router.urls +
    business_product_router.urls +
    product_order_router.urls +
    product_review_router.urls +
    business_service_router.urls +
    branch_service_router.urls +
    branch_service_booking_router.urls +
    branch_service_review_router.urls +
    booking_log_router.urls +
    branch_product_router.urls +
    branch_product_order_router.urls + 
    branch_product_review_router.urls
)


# ============================
# Custom views (non-router)
# ============================

custom_urlpatterns = [
    path("check-domain/", check_domain_availability, name="check-domain"),
    path("nearby-list/", ProductListByProximityView.as_view(), name="product-nearby-list"),
    path("<slug:slug>/url/", generate_product_url, name="generate-product-url"),
    path("public/business/<uuid:pk>/", PublicBusinessDetailView.as_view(), name="public-business-detail"),
    path("nearby/", NearbyEntitiesView.as_view(), name="nearby-entities"),

]


# ============================
# Final urlpatterns
# ============================

urlpatterns = router_urlpatterns + custom_urlpatterns