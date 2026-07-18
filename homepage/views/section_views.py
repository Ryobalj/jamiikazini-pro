# homepage/views/section_views.py

from homepage.views.base import HomePageScopedViewSet, ParentScopedViewSet
from homepage.models.hero_section import HeroSection
from homepage.models.about_section import AboutSection, AboutImage
from homepage.models.what_we_do import WhatWeDo, WhatWeDoService, WhatWeDoImage
from homepage.models.faq import Faq
from homepage.models.testimonial import Testimonial
from homepage.serializers.hero_section_serializer import HeroSectionSerializer
from homepage.serializers.about_section_serializer import AboutSectionSerializer, AboutImageSerializer
from homepage.serializers.what_we_do_serializer import (
    WhatWeDoSerializer, WhatWeDoServiceSerializer, WhatWeDoImageSerializer,
)
from homepage.serializers.faq_serializer import FaqSerializer
from homepage.serializers.testimonial_serializer import TestimonialSerializer


class HeroSectionViewSet(HomePageScopedViewSet):
    queryset = HeroSection.objects.all()
    serializer_class = HeroSectionSerializer


class AboutSectionViewSet(HomePageScopedViewSet):
    queryset = AboutSection.objects.all()
    serializer_class = AboutSectionSerializer


class WhatWeDoViewSet(HomePageScopedViewSet):
    queryset = WhatWeDo.objects.all()
    serializer_class = WhatWeDoSerializer


class FaqViewSet(HomePageScopedViewSet):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer


class TestimonialViewSet(HomePageScopedViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer


class AboutImageViewSet(ParentScopedViewSet):
    queryset = AboutImage.objects.all()
    serializer_class = AboutImageSerializer
    parent_model = AboutSection
    parent_kwarg = 'about_pk'
    parent_field = 'about'


class WhatWeDoServiceViewSet(ParentScopedViewSet):
    queryset = WhatWeDoService.objects.all()
    serializer_class = WhatWeDoServiceSerializer
    parent_model = WhatWeDo
    parent_kwarg = 'whatwedo_pk'
    parent_field = 'what_we_do'


class WhatWeDoImageViewSet(ParentScopedViewSet):
    queryset = WhatWeDoImage.objects.all()
    serializer_class = WhatWeDoImageSerializer
    parent_model = WhatWeDo
    parent_kwarg = 'whatwedo_pk'
    parent_field = 'what_we_do'
