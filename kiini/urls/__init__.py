# kiini/urls/__init__.py

from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter
from kiini.views.institution_views import InstitutionViewSet
from kiini.views.department_views import DepartmentViewSet
from kiini.views.institution_tier_views import InstitutionTierViewSet
from kiini.views.institution_type_views import InstitutionTypeViewSet
from kiini.views.staff_views import StaffProfileViewSet
from kiini.views.institution_public_views import PublicInstitutionDetailView, InstitutionResolveDomainView
from kiini.views.referral_code_views import MyReferralCodeView

app_name = "kiini"

# Root router
router = DefaultRouter()
router.register(r'institutions', InstitutionViewSet, basename='institution')
router.register(r'institution-tiers', InstitutionTierViewSet, basename='institutiontier')
router.register(r'institution-types', InstitutionTypeViewSet, basename='institutiontype')

# Nested routers
institutions_router = NestedDefaultRouter(router, r'institutions', lookup='institution')
institutions_router.register(r'departments', DepartmentViewSet, basename='institution-departments')
institutions_router.register(r'staff-profiles', StaffProfileViewSet, basename='institution-staffprofiles')


urlpatterns = [
    # Must be listed before the router include below - a public detail path
    # with an extra "/public/" suffix doesn't collide with the router's own
    # "institutions/<pk>/" detail route, but keeping custom paths first
    # matches the convention used elsewhere in this codebase.
    path('institutions/<uuid:pk>/public/', PublicInstitutionDetailView.as_view(), name='institution-public-detail'),
    path('institutions/resolve-domain/', InstitutionResolveDomainView.as_view(), name='institution-resolve-domain'),
    path('referral-code/mine/', MyReferralCodeView.as_view(), name='referral-code-mine'),
    path('', include(router.urls)),                      # Main
    path('', include(institutions_router.urls)),           # Nested
    path('', include('kiini.urls.user_menu_urls')),
    path('', include('kiini.urls.ajax_test_urls')),
    path('', include('kiini.urls.notification_urls')),

]




