# homepage/serializers/what_we_do_serializer.py

from rest_framework import serializers

from homepage.models.what_we_do import WhatWeDo, WhatWeDoService, WhatWeDoImage


class WhatWeDoServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatWeDoService
        fields = ['id', 'what_we_do', 'icon', 'title', 'description', 'order', 'is_active', 'created_at']
        read_only_fields = ['id', 'what_we_do', 'created_at']


class WhatWeDoImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatWeDoImage
        fields = ['id', 'what_we_do', 'image', 'caption', 'order', 'is_active', 'created_at']
        read_only_fields = ['id', 'what_we_do', 'created_at']


class WhatWeDoSerializer(serializers.ModelSerializer):
    services = WhatWeDoServiceSerializer(many=True, read_only=True)
    related_images = WhatWeDoImageSerializer(many=True, read_only=True)

    class Meta:
        model = WhatWeDo
        fields = [
            'id', 'homepage', 'title', 'subtitle', 'description', 'image',
            'cta_text', 'cta_link', 'services', 'related_images',
            'order', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'homepage', 'services', 'related_images', 'created_at']
