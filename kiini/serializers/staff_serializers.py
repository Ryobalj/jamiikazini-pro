from rest_framework import serializers
from kiini.models.staff import StaffProfile
from accounts.serializers import MeSerializer

class StaffProfileSerializer(serializers.ModelSerializer):
    user = MeSerializer(read_only=True)

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'institution', 'department',
            'title', 'position', 'phone', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']