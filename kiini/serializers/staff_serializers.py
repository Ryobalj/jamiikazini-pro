from django.contrib.auth import get_user_model
from rest_framework import serializers
from kiini.models.staff import StaffProfile

User = get_user_model()


class StaffProfileSerializer(serializers.ModelSerializer):
    # user ni writable (PK) ili POST iweze kuunda - na representation ni id.
    # Sasa si lazima (blank/null) ili user_email iweze kutumika badala yake -
    # frontend haina UI ya kuchagua User kwa ID moja kwa moja.
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    user_email = serializers.EmailField(write_only=True, required=False)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email_display = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'user_email', 'user_full_name', 'user_email_display',
            'institution', 'department', 'title', 'position', 'phone',
            'is_active', 'created_at'
        ]
        # institution huwekwa na view kutoka nested URL (perform_create)
        read_only_fields = ['id', 'institution', 'created_at', 'user_full_name', 'user_email_display']

    def validate(self, attrs):
        user = attrs.get('user')
        user_email = attrs.pop('user_email', None)
        if not user and user_email:
            try:
                attrs['user'] = User.objects.get(email__iexact=user_email)
            except User.DoesNotExist:
                raise serializers.ValidationError({'user_email': 'Hakuna mtumiaji mwenye barua pepe hii.'})
        if not attrs.get('user') and not self.instance:
            raise serializers.ValidationError({'user_email': 'Weka barua pepe ya mtumiaji.'})
        return attrs