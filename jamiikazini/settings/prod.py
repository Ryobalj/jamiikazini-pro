# jamiikazini/settings/prod.py

import os
from .base import *
from decouple import config

# Environment
DEBUG = False
IS_RENDER_APP = True
TESTING = False

# django-ratelimit inataka shared cache; kwenye free tier (worker 1) LocMemCache
# inatosha, kwa hivyo tunanyamazisha check kama dev. Ikiwa USE_REDIS=true, ondoa.
SILENCED_SYSTEM_CHECKS = [
    "django_ratelimit.E003",
    "django_ratelimit.W001",
]

# Secret Key
SECRET_KEY = config("SECRET_KEY")

# Allowed Hosts
ALLOWED_HOSTS = ["www.jamiikazini.com", ".jamiikazini.com", "jamiikazini.com"]
# Render hutoa RENDER_EXTERNAL_HOSTNAME yenyewe (mfano jamiikazini-pro.onrender.com)
RENDER_EXTERNAL_HOSTNAME = config("RENDER_EXTERNAL_HOSTNAME", default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
# Hosts za ziada kupitia env (comma-separated), mfano "app.onrender.com,example.com"
_extra_hosts = config("ALLOWED_HOSTS", default="")
if _extra_hosts:
    ALLOWED_HOSTS += [h.strip() for h in _extra_hosts.split(",") if h.strip()]

# CSRF: amini Render + domain rasmi (https)
CSRF_TRUSTED_ORIGINS = ["https://*.jamiikazini.com", "https://jamiikazini.com"]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
_extra_csrf = config("CSRF_TRUSTED_ORIGINS", default="")
if _extra_csrf:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra_csrf.split(",") if o.strip()]

# CORS: ruhusu frontend yoyote ya *.onrender.com (dev) + domain rasmi — hivyo
# jina la frontend (hata likiwa na kiambishi kama -1wyv) haliitaji CORS ya mkono.
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.onrender\.com$",
    r"^https://.*\.jamiikazini\.com$",
]

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST", default="localhost"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

# Security settings
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Email settings — zina defaults salama ili app isianguke kama hazijawekwa bado.
# Default = console backend (barua zinaonekana kwenye logs). Weka SMTP halisi ukiwa tayari.
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@jamiikazini.com")
