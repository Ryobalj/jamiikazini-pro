from gov_integration.models import CountryConfig, CountryPolicy, ServiceType

from django.contrib import admin
from .models import (
    ApiEndpoint,
    ServiceConfig,
    VerificationRequest,
    VerificationLog
)

@admin.register(ApiEndpoint)
class ApiEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'base_url', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'base_url')


# Only keep one of the ServiceTypeAdmin registrations.
@admin.register(ServiceType)  # This is the correct way to register.
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'code')


@admin.register(ServiceConfig)
class ServiceConfigAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'is_enabled', 'expires_at')
    list_filter = ('is_enabled',)
    search_fields = ('endpoint__name',)


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'status', 'country', 'created_at', 'updated_at')
    list_filter = ('status', 'country', 'service')
    search_fields = ('user__email', 'institution__name')


@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ('request', 'timestamp', 'success', 'message')
    list_filter = ('success',)


@admin.register(CountryConfig)
class CountryConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'currency', 'integration_ready')
    search_fields = ('name', 'code')


@admin.register(CountryPolicy)
class CountryPolicyAdmin(admin.ModelAdmin):
    list_display = ('country', 'requires_mou', 'requires_license', 'api_access_mode')