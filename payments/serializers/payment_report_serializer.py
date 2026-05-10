# payments/serializers/payment_report_serializer.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from payments.models.payment_report import PaymentReport
from accounts.serializers import UserSerializer

class PaymentReportSerializer(serializers.ModelSerializer):
    """Serializer for detailed payment report view"""
    
    user = UserSerializer(read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_format_display = serializers.CharField(source='get_file_format_display', read_only=True)
    is_ready = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    summary_statistics = serializers.SerializerMethodField(read_only=True)
    progress_display = serializers.SerializerMethodField(read_only=True)
    download_url = serializers.URLField(read_only=True)

    class Meta:
        model = PaymentReport
        fields = [
            # Identifiers
            "id",
            "user",
            
            # Report Type & Status
            "report_type",
            "report_type_display",
            "status", 
            "status_display",
            "progress_percentage",
            "progress_display",
            
            # Date Range
            "start_date",
            "end_date",
            
            # Report Data
            "filters",
            "report_data", 
            "summary",
            "summary_statistics",
            
            # Output & Files
            "file_format",
            "file_format_display",
            "download_url",
            
            # Status Flags
            "is_ready",
            "is_expired",
            
            # Error Handling
            "error_message",
            
            # Timestamps
            "generated_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "user", "created_at", "updated_at", "generated_at", 
            "expires_at", "is_ready", "is_expired", "report_type_display",
            "status_display", "file_format_display", "summary_statistics",
            "progress_display", "download_url"
        ]

    def get_summary_statistics(self, obj):
        """Get formatted summary statistics from report"""
        return obj.get_summary_statistics()

    def get_progress_display(self, obj):
        """Get progress percentage with % symbol"""
        return f"{obj.progress_percentage}%"

    def validate(self, data):
        """Validate report data and date ranges"""
        errors = {}
        
        # Validate date range if both are provided
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                errors['end_date'] = _("End date must be after start date")
            
            # Validate date range doesn't exceed 1 year
            date_range = data['end_date'] - data['start_date']
            if date_range.days > 365:
                errors['end_date'] = _("Report period cannot exceed 1 year")
        
        # Validate progress percentage
        if 'progress_percentage' in data:
            if data['progress_percentage'] < 0 or data['progress_percentage'] > 100:
                errors['progress_percentage'] = _("Progress must be between 0 and 100")
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data

    def create(self, validated_data):
        """Create payment report with user from request context"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        return super().create(validated_data)


class PaymentReportSummarySerializer(serializers.ModelSerializer):
    """Serializer for payment report list view (summary)"""
    
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_ready = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    progress_display = serializers.SerializerMethodField(read_only=True)
    duration_days = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentReport
        fields = [
            "id",
            "report_type",
            "report_type_display",
            "status",
            "status_display",
            "start_date", 
            "end_date",
            "duration_days",
            "progress_percentage",
            "progress_display",
            "is_ready",
            "is_expired",
            "generated_at",
            "file_format",
        ]
        read_only_fields = fields

    def get_progress_display(self, obj):
        """Get progress percentage with % symbol"""
        return f"{obj.progress_percentage}%"

    def get_duration_days(self, obj):
        """Calculate duration of report in days"""
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days
        return 0


class PaymentReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new payment reports"""
    
    class Meta:
        model = PaymentReport
        fields = [
            "report_type",
            "start_date", 
            "end_date",
            "filters",
            "file_format",
        ]
        
    def validate(self, data):
        """Validate creation data"""
        errors = {}
        
        # Ensure date range is provided
        if not data.get('start_date') or not data.get('end_date'):
            errors['non_field_errors'] = _("Both start date and end date are required")
        
        # Validate date range
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                errors['end_date'] = _("End date must be after start date")
            
            # Limit to 1 year maximum
            date_range = data['end_date'] - data['start_date']
            if date_range.days > 365:
                errors['end_date'] = _("Report period cannot exceed 1 year")
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data

    def create(self, validated_data):
        """Create report with user from request context"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        # Set initial status
        validated_data['status'] = PaymentReport.Status.GENERATING
        validated_data['progress_percentage'] = 0
        
        return super().create(validated_data)


class PaymentReportUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payment reports (limited fields)"""
    
    class Meta:
        model = PaymentReport
        fields = [
            "filters",
            "file_format",
        ]
        
    def validate(self, data):
        """Only allow updates for reports that are still generating"""
        instance = self.instance
        
        if instance and instance.status != PaymentReport.Status.GENERATING:
            raise serializers.ValidationError(
                _("Cannot update report that is not in generating status")
            )
        
        return data


class PaymentReportDataSerializer(serializers.ModelSerializer):
    """Serializer for report data only (for API responses)"""
    
    summary_statistics = serializers.SerializerMethodField(read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)

    class Meta:
        model = PaymentReport
        fields = [
            "id",
            "report_type",
            "report_type_display", 
            "report_data",
            "summary",
            "summary_statistics",
            "generated_at",
        ]
        read_only_fields = fields

    def get_summary_statistics(self, obj):
        """Get formatted summary statistics"""
        return obj.get_summary_statistics()


class PaymentReportFilterSerializer(serializers.Serializer):
    """Serializer for report filter parameters"""
    
    report_type = serializers.ChoiceField(
        choices=PaymentReport.ReportType.choices,
        required=False
    )
    status = serializers.ChoiceField(
        choices=PaymentReport.Status.choices, 
        required=False
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    file_format = serializers.ChoiceField(
        choices=[('JSON', 'JSON'), ('CSV', 'CSV'), ('PDF', 'PDF'), ('EXCEL', 'Excel')],
        required=False
    )
    
    def validate(self, data):
        """Validate filter parameters"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': _("End date must be after start date")
                })
        return data