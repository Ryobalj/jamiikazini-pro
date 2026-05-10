# kiini/urls/__init__.py

from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter
from kiini.views.institution_views import InstitutionViewSet
from kiini.views.department_views import DepartmentViewSet
from kiini.views.institution_tier_views import InstitutionTierViewSet
from kiini.views.institution_type_views import InstitutionTypeViewSet
from kiini.views.staff_views import StaffProfileViewSet

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
    path('', include(router.urls)),                      # Main
    path('', include(institutions_router.urls)),           # Nested
    path('', include('kiini.urls.user_menu_urls')),
    path('', include('kiini.urls.ajax_test_urls')),

]




