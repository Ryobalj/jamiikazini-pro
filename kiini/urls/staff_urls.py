# kiini/urls/staff_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from kiini.views.staff_views import StaffProfileViewSet, StaffProfileDetail

router = DefaultRouter()
router.register(r'staff-profiles', StaffProfileViewSet, basename='staffprofile')


urlpatterns = [
    path('', StaffProfileDetail.as_view(), name='staff-profile-detail'),
    path('', include(router.urls)),

]