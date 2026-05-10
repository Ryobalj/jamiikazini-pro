# security/mixins/admin_2fa_mixin.py

from rest_framework.response import Response
from rest_framework import status
from security.decorators import conditional_2fa_required
from functools import wraps

class Admin2FAMixin:
    """
    Enforces 2FA for admin actions:
    create, update, partial_update, destroy
    """

    def dispatch_2fa(self, request, action_func, *args, **kwargs):
        """
        Helper to run 2FA check before executing original action.
        """
        @conditional_2fa_required(action_type="admin_action")
        @wraps(action_func)
        def wrapped(request, *args, **kwargs):
            return action_func(request, *args, **kwargs)
        return wrapped(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self.dispatch_2fa(request, super().create, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self.dispatch_2fa(request, super().update, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.dispatch_2fa(request, super().partial_update, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return self.dispatch_2fa(request, super().destroy, *args, **kwargs)