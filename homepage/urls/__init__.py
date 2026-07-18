# homepage/urls/__init__.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from homepage.views.home_page_views import HomePageViewSet
from homepage.views.my_homepage_views import MyHomePageView
from homepage.views.public_homepage_views import PublicHomePageView
from homepage.views.section_views import (
    HeroSectionViewSet, AboutSectionViewSet, WhatWeDoViewSet, FaqViewSet,
    TestimonialViewSet, AboutImageViewSet, WhatWeDoServiceViewSet, WhatWeDoImageViewSet,
)

app_name = 'homepage'

router = DefaultRouter()
router.register(r'homepages', HomePageViewSet, basename='homepage')

homepage_router = NestedDefaultRouter(router, r'homepages', lookup='homepage')
homepage_router.register(r'hero-sections', HeroSectionViewSet, basename='homepage-hero')
homepage_router.register(r'about-sections', AboutSectionViewSet, basename='homepage-about')
homepage_router.register(r'what-we-do', WhatWeDoViewSet, basename='homepage-whatwedo')
homepage_router.register(r'faqs', FaqViewSet, basename='homepage-faq')
homepage_router.register(r'testimonials', TestimonialViewSet, basename='homepage-testimonial')

about_image_router = NestedDefaultRouter(homepage_router, r'about-sections', lookup='about')
about_image_router.register(r'images', AboutImageViewSet, basename='about-image')

whatwedo_child_router = NestedDefaultRouter(homepage_router, r'what-we-do', lookup='whatwedo')
whatwedo_child_router.register(r'services', WhatWeDoServiceViewSet, basename='whatwedo-service')
whatwedo_child_router.register(r'images', WhatWeDoImageViewSet, basename='whatwedo-image')

urlpatterns = [
    path('mine/<str:owner_type>/<uuid:owner_id>/', MyHomePageView.as_view(), name='my-homepage'),
    path('public/<str:owner_type>/<uuid:owner_id>/', PublicHomePageView.as_view(), name='public-homepage'),
    path('', include(router.urls)),
    path('', include(homepage_router.urls)),
    path('', include(about_image_router.urls)),
    path('', include(whatwedo_child_router.urls)),
]
