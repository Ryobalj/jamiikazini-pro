# security/utils/auth_resolution.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def resolve_authenticated_user(request):
    """
    request.user (kutoka Django's session-based AuthenticationMiddleware) haitambui
    watumiaji wa JWT Bearer token - ambao ndiyo jinsi frontend halisi inavyoauth kila
    request. Bila hii, kila mtumiaji wa JWT angeonekana "hajaingia" popote hapa
    palipotumika, na kupata 401 hata akiwa na token halali kabisa.
    """
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        return user
    try:
        auth_result = JWTAuthentication().authenticate(request)
    except (InvalidToken, TokenError):
        return None
    if auth_result is None:
        return None
    jwt_user, _ = auth_result
    return jwt_user
