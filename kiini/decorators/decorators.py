# kiini/decorators/decirators.py

from functools import wraps
from django.http import JsonResponse

def institution_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request, 'institution', None):
            return JsonResponse({'detail': 'Institution context required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_is_in_institution(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        institution = getattr(request, 'institution', None)

        if not user.is_authenticated:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        if user.role != 'ADMIN' and (not institution or user.institution_id != institution.id):
            return JsonResponse({'detail': 'Access denied. Wrong institution context.'}, status=403)

        return view_func(request, *args, **kwargs)
    return _wrapped_view
    
def admin_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response({"detail": "Not authorized."}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view