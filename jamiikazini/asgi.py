"""
ASGI config for jamiikazini project.

It exposes the ASGI callable as a module-level variable named ``application``.
Inashughulikia HTTP ya kawaida (Django) + WebSocket (Django Channels, kwa
jamiichat real-time messaging).

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

# Chagua settings kulingana na mazingira
ENVIRONMENT = os.getenv("DJANGO_ENV", "dev")  # default ni dev

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"jamiikazini.settings.{ENVIRONMENT}")

from django.core.asgi import get_asgi_application

# django_asgi_app LAZIMA ipatikane kabla ya kuagiza chochote kinachogusa
# models (routing.py -> consumers.py -> models) - vinginevyo AppRegistryNotReady.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from jamiichat.routing import websocket_urlpatterns  # noqa: E402
from jamiichat.ws_auth import JWTAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
