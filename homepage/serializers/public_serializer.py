# homepage/serializers/public_serializer.py

from rest_framework import serializers

from homepage.serializers.hero_section_serializer import HeroSectionSerializer
from homepage.serializers.about_section_serializer import AboutSectionSerializer
from homepage.serializers.what_we_do_serializer import WhatWeDoSerializer
from homepage.serializers.faq_serializer import FaqSerializer
from homepage.serializers.testimonial_serializer import TestimonialSerializer


class PublicHomePageSerializer(serializers.Serializer):
    """Muhtasari wa umma - HomePage + sections zote hai, kwa mpangilio."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    tagline = serializers.CharField()
    logo = serializers.ImageField()
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField()
    contact_address = serializers.CharField()
    social_facebook = serializers.URLField()
    social_instagram = serializers.URLField()
    social_twitter = serializers.URLField()
    social_whatsapp = serializers.CharField()
    primary_color = serializers.CharField()
    secondary_color = serializers.CharField()

    hero_sections = serializers.SerializerMethodField()
    about_sections = serializers.SerializerMethodField()
    what_we_do_sections = serializers.SerializerMethodField()
    faqs = serializers.SerializerMethodField()
    testimonials = serializers.SerializerMethodField()

    def get_hero_sections(self, obj):
        qs = obj.hero_sections.filter(is_active=True).order_by('order', '-created_at')
        return HeroSectionSerializer(qs, many=True, context=self.context).data

    def get_about_sections(self, obj):
        qs = obj.about_sections.filter(is_active=True).order_by('order', '-created_at')
        return AboutSectionSerializer(qs, many=True, context=self.context).data

    def get_what_we_do_sections(self, obj):
        qs = obj.what_we_do_sections.filter(is_active=True).order_by('order', '-created_at')
        return WhatWeDoSerializer(qs, many=True, context=self.context).data

    def get_faqs(self, obj):
        qs = obj.faqs.filter(is_active=True).order_by('order', '-created_at')
        return FaqSerializer(qs, many=True, context=self.context).data

    def get_testimonials(self, obj):
        qs = obj.testimonials.filter(is_active=True).order_by('order', '-created_at')
        return TestimonialSerializer(qs, many=True, context=self.context).data
