# homepage/serializers/hero_section_serializer.py

from rest_framework import serializers

from homepage.models.hero_section import HeroSection


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = [
            'id', 'homepage', 'title', 'subtitle', 'background_image',
            'cta_text', 'cta_link', 'order', 'is_active', 'created_at',
        ]
        # homepage huwekwa na view kutoka nested URL (perform_create) - bila
        # kuifanya read-only, POST ingedai homepage mwilini (400)
        read_only_fields = ['id', 'homepage', 'created_at']
