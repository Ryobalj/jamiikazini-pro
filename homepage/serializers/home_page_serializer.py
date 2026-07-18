# homepage/serializers/home_page_serializer.py

from rest_framework import serializers

from homepage.models.home_page import HomePage


class HomePageSerializer(serializers.ModelSerializer):
    owner_type = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()

    class Meta:
        model = HomePage
        fields = [
            'id', 'name', 'tagline', 'logo',
            'contact_email', 'contact_phone', 'contact_address',
            'social_facebook', 'social_instagram', 'social_twitter', 'social_whatsapp',
            'primary_color', 'secondary_color', 'is_published',
            'owner_type', 'owner_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner_type', 'owner_id', 'created_at', 'updated_at']

    def get_owner_type(self, obj):
        return obj.content_type.model

    def get_owner_id(self, obj):
        return str(obj.object_id)
