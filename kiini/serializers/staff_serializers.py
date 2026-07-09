from django.contrib.auth import get_user_model
from rest_framework import serializers
from kiini.models.staff import StaffProfile

User = get_user_model()


class StaffProfileSerializer(serializers.ModelSerializer):
    # user ni writable (PK) ili POST iweze kuunda - na representation ni id
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'institution', 'department',
            'title', 'position', 'phone', 'is_active', 'created_at'
        ]
        # institution huwekwa na view kutoka nested URL (perform_create)
        read_only_fields = ['id', 'institution', 'created_at']