# gov_integration/serializers/service_type.py

from rest_framework import serializers
from gov_integration.models import VerificationRequest, ServiceType
from kiini.models import Institution
from .country_config import CountryConfigSerializer

class ServiceTypeSerializer(serializers.ModelSerializer):
    country = CountryConfigSerializer(read_only=True)

    class Meta:
        model = ServiceType
        fields = ['id', 'name', 'code', 'description', 'country', 'is_active']

class VerificationRequestSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=ServiceType.objects.all())
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all(), required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = VerificationRequest
        fields = [
            'id',
            'user',
            'institution',
            'country',
            'service',
            'payload',
            'status',
            'response_data',
            'created_at',
        ]
        read_only_fields = ['status', 'response_data', 'created_at']
