# logistics/serializers/driver_serializer.py

from rest_framework import serializers
from logistics.models.driver import Driver
from kiini.helpers.domain import generate_subdomain_url

class DriverSerializer(serializers.ModelSerializer):
    provider_url = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            'id', 'transport_provider', 'full_name', 'license_number',
            'phone_number', 'profile_image', 'is_verified',
            'is_active', 'created_at', 'updated_at', 'provider_url'
        ]
        read_only_fields = ['id', 'transport_provider', 'is_verified', 'created_at', 'updated_at']

    def validate_license_number(self, value):
        if self.instance:
            if Driver.objects.exclude(id=self.instance.id).filter(license_number=value).exists():
                raise serializers.ValidationError("Leseni hii tayari imesajiliwa.")
        else:
            if Driver.objects.filter(license_number=value).exists():
                raise serializers.ValidationError("Leseni hii tayari imesajiliwa.")
        return value

    def get_provider_url(self, obj):
        try:
            domain = obj.transport_provider.institution.domain
            request = self.context.get("request")
            path = f"/api/logistics/providers/{obj.transport_provider.id}/"  # adjust this path if needed
            return generate_subdomain_url(domain, request, path)
        except Exception:
            return None