# gov_integration/serializers/transport_verification_serializers.py

from rest_framework import serializers


class NIDAVerificationSerializer(serializers.Serializer):
    national_id_number = serializers.CharField()

    def to_representation(self, instance):
        return {"payload": {"national_id_number": instance["national_id_number"]}}


class DriverLicenseVerificationSerializer(serializers.Serializer):
    license_number = serializers.CharField()

    def to_representation(self, instance):
        return {"payload": {"license_number": instance["license_number"]}}


class BusinessLicenseVerificationSerializer(serializers.Serializer):
    business_license_number = serializers.CharField()

    def to_representation(self, instance):
        return {"payload": {"business_license_number": instance["business_license_number"]}}


class LatraLicenseVerificationSerializer(serializers.Serializer):
    latra_license_number = serializers.CharField()

    def to_representation(self, instance):
        return {"payload": {"latra_license_number": instance["latra_license_number"]}}