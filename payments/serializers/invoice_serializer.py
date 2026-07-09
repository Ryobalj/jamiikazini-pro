# payments/serializers/invoice_serializer.py

from rest_framework import serializers
from payments.models.invoice import Invoice, InvoiceStatus
from accounts.serializers import SimpleUserSerializer

class InvoiceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)  # 🔹 force id kuwa string
    invoice_number = serializers.CharField(read_only=True)  # 🔹 automatic
    user = SimpleUserSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    last_modified_by = SimpleUserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    # description ni property (encrypted _description) - bila hii DRF angeifanya read-only kimya
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # 🔹 Decimal fields kama strings
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, coerce_to_string=True)
    tax = serializers.DecimalField(max_digits=14, decimal_places=2, coerce_to_string=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, coerce_to_string=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'user', 'amount', 'tax',
            'total_amount', 'status', 'status_display',
            'due_date', 'paid_at', 'description',
            'created_by', 'last_modified_by',
            'is_overdue', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'invoice_number', 'total_amount', 'status_display',
            'created_at', 'updated_at', 'is_overdue'
        ]

    def validate_due_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date haiwezi kuwa tarehe iliyopita.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Kiasi cha invoice lazima kiwe zaidi ya sifuri.")
        return value

    def validate_tax(self, value):
        if value < 0:
            raise serializers.ValidationError("Kodi haiwezi kuwa hasi.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = validated_data.get('user', request.user)
            validated_data['created_by'] = request.user
            validated_data['last_modified_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['last_modified_by'] = request.user
        return super().update(instance, validated_data)