# jamiiwallet/serializers/budget_serializer.py

from rest_framework import serializers

from jamiiwallet.models.budget import Budget


class BudgetSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    spent_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    is_over_budget = serializers.BooleanField(read_only=True)

    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'category_display', 'period', 'amount', 'is_active',
            'spent_amount', 'remaining_amount', 'is_over_budget', 'created_at',
        ]
        read_only_fields = [
            'id', 'category_display', 'spent_amount', 'remaining_amount',
            'is_over_budget', 'created_at',
        ]

    def get_spent_amount(self, obj):
        return obj.spent_amount()

    def get_remaining_amount(self, obj):
        return obj.remaining_amount

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        wallet = self.context['request'].user.wallet
        return Budget.objects.create(wallet=wallet, **validated_data)
