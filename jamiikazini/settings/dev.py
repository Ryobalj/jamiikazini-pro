# jamiikazini/settings/dev.py

from .base import *


# INSTALLED_APPS += [
#     "debug_toolbar",
# ]

# MIDDLEWARE += [
#     "debug_toolbar.middleware.DebugToolbarMiddleware",
# ]

INTERNAL_IPS = ["127.0.0.1"]

# Local dev runs without Redis; the locmem cache is fine for a single
# runserver process even though django_ratelimit flags it as non-shared.
SILENCED_SYSTEM_CHECKS = [
    "django_ratelimit.E003",
    "django_ratelimit.W001",
]

# Database (Local development)
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": config("POSTGRES_DB", default="jamiikazini"),
        "USER": config("POSTGRES_USER", default="postgres"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="postgres"),
        "HOST": config("POSTGRES_HOST", default="localhost"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

INTERNAL_IPS = ["127.0.0.1"]
