# homepage/serializers/faq_serializer.py

from rest_framework import serializers

from homepage.models.faq import Faq


class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = ['id', 'homepage', 'question', 'answer', 'order', 'is_active', 'created_at']
        read_only_fields = ['id', 'homepage', 'created_at']
