# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, LoginHistory
from accounts.forms import UserAdminForm
from django.contrib import messages


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm

    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = self.form
        form = super().get_form(request, obj, **kwargs)

        class FormWithRequest(form):
            def __new__(cls, *args, **kw):
                kw['request'] = request
                return form(*args, **kw)

        return FormWithRequest

    def get_fieldsets(self, request, obj=None):
        """Dynamic fieldsets based on whether user is viewing themselves"""
        
        # Base fieldsets - always shown
        base_fieldsets = [
            (None, {'fields': ('email', 'password')}),
            ('Permissions', {
                'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            }),
            ('Security', {'fields': ('is_verified', 'is_2fa_enabled')}),
        ]
        
        # Personal info fields
        personal_fields = ['full_name', 'role', 'institution']
        
        # Sensitive fields - only for self
        if obj and request.user.pk == obj.pk:
            personal_fields.extend(['phone_number', 'device_token', 'national_id'])
        
        base_fieldsets.insert(1, ('Personal Info', {'fields': personal_fields}))
        
        return base_fieldsets

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'full_name', 'role', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('email',)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and str(request.user.pk) != str(object_id):
            messages.warning(
                request,
                "⚠️ Huwezi kuona wala kuhariri taarifa nyeti za mtumiaji mwingine, hata kama wewe ni msimamizi."
            )
        else:
            messages.info(
                request,
                "✅ Unaweza kuona na kuhariri taarifa zako nyeti binafsi."
            )
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_time', 'was_successful')
    list_filter = ('was_successful', 'login_time')
    search_fields = ('user__email', 'ip_address')