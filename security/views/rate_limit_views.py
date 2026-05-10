# security/views/rate_limit_views.py

from django.http import JsonResponse

def ratelimited_view(request, exception=None):
    return JsonResponse({'detail': 'Too many requests'}, status=429)