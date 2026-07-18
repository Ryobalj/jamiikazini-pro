# homepage/serializers/testimonial_serializer.py

from rest_framework import serializers

from homepage.models.testimonial import Testimonial


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = [
            'id', 'homepage', 'client_name', 'client_role', 'client_image',
            'content', 'rating', 'order', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'homepage', 'created_at']
