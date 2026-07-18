# homepage/serializers/about_section_serializer.py

from rest_framework import serializers

from homepage.models.about_section import AboutSection, AboutImage


class AboutImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutImage
        fields = ['id', 'about', 'image', 'caption', 'order', 'is_active', 'created_at']
        read_only_fields = ['id', 'about', 'created_at']


class AboutSectionSerializer(serializers.ModelSerializer):
    gallery = AboutImageSerializer(many=True, read_only=True)

    class Meta:
        model = AboutSection
        fields = [
            'id', 'homepage', 'title', 'description', 'mission', 'vision',
            'image', 'stats', 'gallery', 'order', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'homepage', 'gallery', 'created_at']
