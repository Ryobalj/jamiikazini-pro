# helpers/request.py

def get_client_ip(request):
    """
    Extract client IP address from request headers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_user_agent(request):
    """
    Extract User-Agent string from request headers.
    """
    return request.META.get('HTTP_USER_AGENT', '')
