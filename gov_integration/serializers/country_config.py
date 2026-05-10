from rest_framework import serializers
from gov_integration.models import CountryConfig, CountryPolicy

class CountryPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryPolicy
        fields = '__all__'

class CountryConfigSerializer(serializers.ModelSerializer):
    policy = CountryPolicySerializer(read_only=True)

    class Meta:
        model = CountryConfig
        fields = ['id', 'code', 'name', 'currency', 'integration_ready', 'default_language', 'notes', 'policy']