# kiini/urls/institution_urls.py

from rest_framework.routers import DefaultRouter
from kiini.views.institution_views import InstitutionViewSet
from kiini.views.department_views import DepartmentViewSet
from kiini.views.institution_type_views import InstitutionTypeViewSet
from kiini.views.institution_tier_views import InstitutionTierViewSet


router = DefaultRouter()
router.register(r'institutions', InstitutionViewSet, basename='institution')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'institution-types', InstitutionTypeViewSet, basename='institutiontype')
router.register(r'institution-tiers', InstitutionTierViewSet, basename='institutiontier')


urlpatterns = router.urls
