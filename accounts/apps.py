# accounts/apps.py

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Import signals only (avoid DB queries here)
        from . import signals