# businesses/serializers/review_serializer.py

from rest_framework import serializers
from businesses.models.review import Review
from businesses.validators.review_validators import validate_unique_review


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'user',
            'business',
            'product',
            'service',
            'rating',
            'content',
            'is_approved',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'is_approved', 'created_at']
        extra_kwargs = {
            'user': {'required': False},
            'business': {'required': False},
            'product': {'required': False},
            'service': {'required': False},
        }

    def validate(self, data):
        """Hakikisha review ni sahihi wakati wa CREATE pekee."""
        request = self.context.get("request")
        user = request.user if request else None

        # Hakikisha user amelogin wakati wa CREATE
        if self.instance is None:
            if user is None or not user.is_authenticated:
                raise serializers.ValidationError("Lazima uingie kwanza kabla ya kuongeza review.")

            # Hakikisha ni target moja tu
            targets = [data.get('business'), data.get('product'), data.get('service')]
            filled = [t for t in targets if t is not None]
            if len(filled) != 1:
                raise serializers.ValidationError(
                    "Tafadhali toa review kwa kipengele kimoja tu: biashara, bidhaa, au huduma."
                )
            # Angalia uniqueness wakati wa CREATE
            validate_unique_review(
                user,
                product=data.get("product"),
                service=data.get("service"),
                business=data.get("business"),
            )
        return data

    def create(self, validated_data):
        """Hakikisha user imewekwa wakati review inaundwa."""
        request = self.context.get("request")
        user = request.user if request else None
        validated_data["user"] = user
        return super().create(validated_data)

    def to_representation(self, instance):
        """Onyesha review na target kamili."""
        rep = super().to_representation(instance)
        target = instance.service or instance.product or instance.business
        rep["target"] = str(target)
        rep["username"] = instance.user.username
        return rep