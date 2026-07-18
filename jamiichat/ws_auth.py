# jamiichat/ws_auth.py

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user_from_token(token):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        validated = AccessToken(token)
        return User.objects.get(id=validated['user_id'])
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Inathibitisha muunganisho wa WebSocket kwa JWT access token kupitia
    query string (?token=...) - kivinjari hakiwezi kutuma Authorization
    header ya kawaida kwenye WebSocket handshake.
    """

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope.get('query_string', b'').decode())
        token = query_string.get('token', [None])[0]
        scope['user'] = await _get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
