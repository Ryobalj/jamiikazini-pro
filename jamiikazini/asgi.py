"""
ASGI config for jamiikazini project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

# Chagua settings kulingana na mazingira
ENVIRONMENT = os.getenv("DJANGO_ENV", "dev")  # default ni dev

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"jamiikazini.settings.{ENVIRONMENT}")

from django.core.asgi import get_asgi_application

application = get_asgi_application()