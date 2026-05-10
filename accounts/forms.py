# accounts/forms.py

from django import forms
from accounts.models import User

class UserAdminForm(forms.ModelForm):
    phone_number = forms.CharField(required=False)
    device_token = forms.CharField(required=False)
    national_id = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        instance = self.instance

        if instance and instance.pk and self.request:
            if instance.pk == self.request.user.pk:
                # User mwenyewe - show everything
                self.fields['phone_number'].initial = instance.phone_number
                self.fields['device_token'].initial = instance.device_token
                self.fields['national_id'].initial = instance.national_id
                self.fields['email'].initial = instance.email

                if instance.phone_number:
                    self.fields['phone_number'].widget.attrs['placeholder'] = self._mask(instance.phone_number)
                if instance.national_id:
                    self.fields['national_id'].widget.attrs['placeholder'] = self._mask(instance.national_id)
                if instance.device_token:
                    self.fields['device_token'].widget.attrs['placeholder'] = self._mask(instance.device_token)
                if instance.email:
                    self.fields['email'].widget.attrs['placeholder'] = self._mask_email(instance.email)
            else:
                # User mwingine - remove sensitive fields from form
                self.fields.pop('phone_number', None)
                self.fields.pop('device_token', None)
                self.fields.pop('national_id', None)
                # Email stays but readonly
                self.fields['email'].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.request and instance.pk == self.request.user.pk:
            phone = self.cleaned_data.get('phone_number')
            token = self.cleaned_data.get('device_token')
            nin = self.cleaned_data.get('national_id')
            email = self.cleaned_data.get('email')

            if phone:
                instance.phone_number = phone
            if nin:
                instance.national_id = nin
            if token:
                instance.device_token = token
            if email:
                instance.email = email

        if commit:
            instance.save()
        return instance

    def _mask(self, value):
        if value and len(value) > 5:
            return value[:4] + '*' * (len(value) - 6) + value[-2:]
        return '*****'

    def _mask_email(self, email):
        if not email:
            return ''
        parts = email.split('@')
        if len(parts[0]) > 3:
            return parts[0][:3] + '••••@' + parts[1]
        return '••••@' + parts[1]