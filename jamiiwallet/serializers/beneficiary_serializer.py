# jamiiwallet/serializers/beneficiary_serializer.py

from rest_framework import serializers

from jamiiwallet.models.beneficiary import Beneficiary
from jamiiwallet.serializers.transfer_serializer import find_recipient


class BeneficiarySerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiary
        fields = ['id', 'name', 'identifier', 'is_favorite', 'is_registered', 'created_at']
        read_only_fields = ['id', 'is_registered', 'created_at']

    def get_is_registered(self, obj):
        return obj.linked_user_id is not None

    def validate_identifier(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Weka namba ya simu au barua pepe.")
        return value

    def create(self, validated_data):
        owner = self.context["request"].user
        linked_user = find_recipient(validated_data.get("identifier"))
        return Beneficiary.objects.create(owner=owner, linked_user=linked_user, **validated_data)
