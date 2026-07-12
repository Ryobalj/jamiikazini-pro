# jamiiwallet/serializers/expense_serializer.py

from rest_framework import serializers

from jamiiwallet.models.expense import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'amount', 'category', 'category_display', 'note', 'incurred_at', 'created_at']
        read_only_fields = ['id', 'category_display', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        request = self.context['request']
        wallet = request.user.wallet
        return Expense.objects.create(wallet=wallet, recorded_by=request.user, **validated_data)
