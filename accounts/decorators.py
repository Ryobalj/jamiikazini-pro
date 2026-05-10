# accounts/decorators.py

from rest_framework.response import Response
from rest_framework import status
from functools import wraps

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or user.role != role:
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator