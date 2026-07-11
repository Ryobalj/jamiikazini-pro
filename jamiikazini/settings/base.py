# jamiikazini/settings/base.py

import os
import sys
import logging
from pathlib import Path
from decouple import config
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from corsheaders.defaults import default_headers

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


# ===========================
# Basic Configuration
# ===========================
# True under pytest even when settings load before conftest sets TESTING=True
TESTING = (
    os.environ.get('TESTING') == 'True'
    or 'pytest' in sys.modules
    or any('pytest' in arg for arg in sys.argv[:1])
)
DJANGO_ENV = config("DJANGO_ENV", default="development")

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

# Logger setup
logger = logging.getLogger(__name__)

# Environment flags
SECRET_KEY = config("SECRET_KEY", default="fallback-key")
IS_RENDER_APP = config("RENDER", default=False, cast=bool)
DEBUG = config("DEBUG", default=False, cast=bool)
RATELIMIT_RATE = config("RATELIMIT_RATE", "5/m")


# ===========================
# Cache & Redis Settings
# ===========================
USE_REDIS = config("USE_REDIS", default=False, cast=bool)
REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/1")


# ===========================
# Third-Party Service Keys
# ===========================
RECAPTCHA_PUBLIC_KEY = config("RECAPTCHA_PUBLIC_KEY_V2", default="")
RECAPTCHA_PRIVATE_KEY = config("RECAPTCHA_PRIVATE_KEY_V2", default="")

RECAPTCHA_PUBLIC_KEY_V3 = config("RECAPTCHA_PUBLIC_KEY_V3", default="")
RECAPTCHA_PRIVATE_KEY_V3 = config("RECAPTCHA_PRIVATE_KEY_V3", default="")

# Email
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@jamiikazini.com")

# SMS Settings
SMS_PROVIDER_API_KEY = config("SMS_PROVIDER_API_KEY", default="")
SMS_PROVIDER_URL = config("SMS_PROVIDER_URL", default="")

# Push Notifications Settings
FCM_API_KEY = config("FCM_API_KEY", default="")
FCM_SENDER_ID = config("FCM_SENDER_ID", default="")

# Chat Settings
CHAT_SERVER_URL = config("CHAT_SERVER_URL", default="http://chat.jamiikazini.com")

# Media Storage (S3)
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="")

# Encryption
FERNET_SECRET_KEY = config("FERNET_SECRET_KEY", default="").encode()


# ===========================
# Allowed Hosts & CORS
# ===========================
DEV_HOSTS = config("DEV_HOSTS", default="localhost,127.0.0.1").split(",")
ALLOWED_HOSTS = (
    ["www.jamiikazini.com", ".jamiikazini.com", "jamiikazini.com"]
    if IS_RENDER_APP else
    DEV_HOSTS
)

if TESTING:
    # subdomain-isolation tests hit hosts like test.localhost
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + [".localhost", "testserver"]

# ===========================
# Application Definition
# ===========================
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.gis",

    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_yasg",
    "phonenumber_field",
    "django_countries",
    "django_filters",
    "corsheaders",
    "django_ratelimit",
    "django_extensions",
    'django_elasticsearch_dsl',
    'modeltranslation',
    "django_recaptcha",
    "widget_tweaks",
    "nested_admin",

    # Local apps
    "accounts.apps.AccountsConfig",
    "kiini.apps.KiiniConfig",
    "institutions.apps.InstitutionsConfig",
    "businesses.apps.BusinessesConfig",
    "logistics.apps.LogisticsConfig",
    "payments.apps.PaymentsConfig",
    "search.apps.SearchConfig",
    "gov_integration.apps.GovIntegrationConfig",
    "jamiichat.apps.JamiichatConfig",
    "jamiiwallet.apps.JamiiwalletConfig",
    "education.apps.EducationConfig",
    "health.apps.HealthConfig",
    "security.apps.SecurityConfig",
    "jamiitasks.apps.JamiitasksConfig",
    "syllabus.apps.SyllabusConfig",
    "portifolio.apps.PortifolioConfig",
]


# ===========================
# Middleware
# ===========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "kiini.middleware.geolocation_language.GeoLocationLanguageMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "security.middleware.conditional_2fa.Conditional2FAMiddleware",
    "kiini.middleware.institution.InstitutionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
]


# ===========================
# Site & Domain
# ===========================
SITE_ID = 1
CENTRAL_DOMAIN = config("DOMAIN_BASE", default="jamiikazini.com")
INSTITUTION_REQUIRED_URLS_EXEMPT = [
    "/admin/",
    "/favicon",
    "/static/",
    "/docs/",
    "/auth/token/",
    "/auth/token/refresh/",
    "/auth/token/verify/",
    "/auth/token/blacklist/",
]

ROOT_URLCONF = 'jamiikazini.urls'
WSGI_APPLICATION = 'jamiikazini.wsgi.application'


# ===========================
# Internationalization
# ===========================
LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", _("English")),
    ("sw", _("Swahili")),
    ("fr", _("French")),
    ("ar", _("Arabic")),
]

TIME_ZONE = "Africa/Nairobi"

USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]
GEOIP_PATH = BASE_DIR / "geoip"

# Modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en",)
MODELTRANSLATION_LANGUAGES = ("en", "sw", "fr", "ar")

LANGUAGE_COOKIE_NAME = "jamiikazini_language"


# ===========================
# Static & Media Files
# ===========================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, "tmp")
# Hakikisha dir ipo (Render/Linux haina 'tmp' ya project kwa default) -> zuia files.E001
os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ===========================
# Authentication & Security
# ===========================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = '/account/two_factor/'

# Security Headers
if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
else:
    SESSION_COOKIE_SECURE = False

CSRF_COOKIE_SECURE = not DEBUG  # True in production, False in development


# ===========================
# DRF Configuration
# ===========================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema',
    "DEFAULT_THROTTLE_CLASSES": [
        "security.authentication.throttling.JamiiThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "security_authentication_throttle": "10000/day",
    }
}


# ===========================
# JWT Settings
# ===========================
SIMPLE_JWT = {
    # Muda mrefu wa kuepuka usumbufu (refresh za mara kwa mara). Env-configurable.
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config("ACCESS_TOKEN_MINUTES", default=120, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config("REFRESH_TOKEN_DAYS", default=30, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_USER_CLASS': 'accounts.models.User',
    'SIGNING_KEY': SECRET_KEY,
    'UPDATE_LAST_LOGIN': True,
}


# ===========================
# CORS Settings
# ===========================
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = list(set(
    config(
        "CORS_ALLOWED_ORIGINS",
        default="http://localhost:5173,http://localhost:3000,https://jamiikazini.com"
    ).split(",") +
    ["http://127.0.0.1:5173", "http://localhost:5173", "http://localhost:3000", "https://jamiikazini.com"]
))

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-request-id',
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://localhost:3000",
    "https://jamiikazini.com",
]


# ===========================
# Templates
# ===========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ===========================
# Phone & Currency
# ===========================
PHONENUMBER_DEFAULT_REGION = "TZ"
DEFAULT_CURRENCY = "TZS"


# ===========================
# Rate Limiting
# ===========================
RATELIMIT_VIEW = 'security.views.rate_limit_views.ratelimited_view'


# ===========================
# Swagger Settings
# ===========================
SWAGGER_USE_COMPAT_RENDERERS = False


# ===========================
# GDAL / GEOS (GeoDjango)
# ===========================
# Windows (local dev): tumia njia za OSGeo4W kwa default.
# Linux/Render: acha None ili GeoDjango itafute libgdal.so / libgeos_c.so za mfumo
# yenyewe (au weka env var GDAL_LIBRARY_PATH / GEOS_LIBRARY_PATH ikiwa njia ni maalum).
if os.name == 'nt':
    GDAL_LIBRARY_PATH = config('GDAL_LIBRARY_PATH', default=r'C:\OSGeo4W\bin\gdal312.dll')
    GEOS_LIBRARY_PATH = config('GEOS_LIBRARY_PATH', default=r'C:\OSGeo4W\bin\geos_c.dll')
else:
    GDAL_LIBRARY_PATH = config('GDAL_LIBRARY_PATH', default=None)
    GEOS_LIBRARY_PATH = config('GEOS_LIBRARY_PATH', default=None)


# ===========================
# Cache Configuration
# ===========================
if USE_REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "COMPRESS_MIN_LEN": 64,
                "CONNECTION_POOL_KWARGS": {"max_connections": 100, "retry_on_timeout": True},
                "SOCKET_CONNECT_TIMEOUT": 2,
                "SOCKET_TIMEOUT": 2,
            },
            "TIMEOUT": 300,
            "KEY_PREFIX": "jamiikazini",
            "VERSION": 1,
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
            "TIMEOUT": 300,
        }
    }


# ===========================
# Celery Configuration
# ===========================
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

if TESTING:
    # Run tasks synchronously during tests: without a broker every .delay()
    # blocks in kombu's connection-retry backoff (~1 min per call).
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_CONNECTION_RETRY = False
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False

# Production/free-tier: endesha tasks papo hapo (synchronous) ndani ya process
# yenyewe pale CELERY_TASK_ALWAYS_EAGER=true. Hii huruhusu app ikimbie kikamilifu
# kwenye Render bila worker ya kulipia wala Redis broker.
elif config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool):
    CELERY_TASK_ALWAYS_EAGER = True
    # EAGER_PROPAGATES=False: task ya nyuma ikishindwa haivunji request ya mtumiaji.
    CELERY_TASK_EAGER_PROPAGATES = config("CELERY_TASK_EAGER_PROPAGATES", default=False, cast=bool)
    CELERY_BROKER_CONNECTION_RETRY = False
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # === EXCHANGE RATES ===
    "update-exchange-rates-daily": {
        "task": "jamiitasks.tasks.exchange_rate_tasks.update_exchange_rates_task",
        "schedule": crontab(hour=12, minute=0),
        "args": ("BOT", "TZS", None),
    },

    # === PAYMENT AUTOMATION ===
    "process-scheduled-payments-hourly": {
        "task": "jamiitasks.tasks.payment_tasks.process_scheduled_payments",
        "schedule": 3600.0,
    },
    
    "execute-daily-payment-automation": {
        "task": "jamiitasks.tasks.payment_tasks.execute_daily_payment_automation",
        "schedule": crontab(hour=0, minute=0),
    },
    
    "cleanup-expired-payment-links": {
        "task": "jamiitasks.tasks.payment_tasks.cleanup_expired_payment_links",
        "schedule": 43200.0,
    },
    
    "generate-payment-reports": {
        "task": "jamiitasks.tasks.payment_tasks.generate_payment_reports",
        "schedule": crontab(hour=1, minute=0),
    },

    # === PAYMENT HEALTH ===
    "retry-failed-payments": {
        "task": "jamiitasks.tasks.payment_tasks.retry_failed_payments",
        "schedule": 1800.0,
    },
    
    "payment-health-check": {
        "task": "jamiitasks.tasks.payment_tasks.coordinate_payment_health_check",
        "schedule": 7200.0,
    },
    
    "compensate-stuck-transactions": {
        "task": "jamiitasks.tasks.payments_gateway_tasks.compensate_stuck_transactions",
        "schedule": 7200.0,
    },

    # === GATEWAY AUTOMATION ===
    "poll-pending-transactions": {
        "task": "jamiitasks.tasks.payments_gateway_tasks.poll_pending_transactions",
        "schedule": 120.0,
    },
    
    "failover-stuck-transactions": {
        "task": "jamiitasks.tasks.payments_gateway_tasks.failover_wallet_payment",
        "schedule": 3600.0,
    },

    # === WALLET TASKS ===
    "retry-failed-topups": {
        "task": "jamiitasks.tasks.payment_tasks.retry_failed_topups",
        "schedule": 3600.0,
    },

    # === SECURITY & MONITORING ===
    "security-cleanup-expired-otps": {
        "task": "jamiitasks.tasks.security_tasks.cleanup_expired_otps",
        "schedule": 86400.0,
    },

    "security-log-rotation": {
        "task": "jamiitasks.tasks.security_tasks.run_audit_log_rotation",
        "schedule": 43200.0,
    },
    
    "distributed-scheduled-payments": {
        "task": "jamiitasks.tasks.distributed_payment_tasks.process_scheduled_payments",
        "schedule": 300.0,
    },
}


# ===========================
# Payment Gateway Configuration
# ===========================
# PawaPay
# NB: PawaPayGateway client hutafuta settings.PAWAPAY_SANDBOX_API_KEY /
# PAWAPAY_LIVE_API_KEY moja kwa moja — kwa hivyo tunazifafanua hapa kutoka .env.
PAWAPAY_SANDBOX_API_KEY = config("PAWAPAY_SANDBOX_API_KEY", default="")
PAWAPAY_LIVE_API_KEY = config("PAWAPAY_LIVE_API_KEY", default="")

PAWAPAY = {
    "SANDBOX_URL": "https://sandbox.pawapay.cloud",
    "LIVE_URL": "https://api.pawapay.cloud",
    "API_KEY": config("PAWAPAY_API_KEY", default="") or PAWAPAY_SANDBOX_API_KEY,
    "CALLBACK_URL": config("PAWAPAY_CALLBACK_URL", default=""),
    "USE_SANDBOX": config("PAWAPAY_USE_SANDBOX", cast=bool, default=True),
    "WEBHOOK_SECRET": config("PAWAPAY_WEBHOOK_SECRET", default=""),
}

# Ramani ya MNO (mtandao) -> PawaPay provider code (Tanzania). Thibitisha dhidi ya
# PawaPay active-configuration ya akaunti yako ikibidi.
PAWAPAY_PROVIDERS = {
    "tigo": "TIGO_TZA",
    "yas": "TIGO_TZA",        # Yas = jina jipya la Tigo
    "airtel": "AIRTEL_TZA",
    "halotel": "HALOTEL_TZA",
    "vodacom": "VODACOM_TZA",  # M-Pesa (ikiwezeshwa baadaye)
}
# Sarafu chaguo-msingi kwa malipo ya mobile money (Tanzania)
PAWAPAY_DEFAULT_CURRENCY = config("PAWAPAY_DEFAULT_CURRENCY", default="TZS")

# Flutterwave
FLUTTERWAVE = {
    "SANDBOX_URL": "https://api.sandbox.flutterwave.com/v3",
    "LIVE_URL": "https://api.flutterwave.com/v3",
    "API_KEY": config("FLUTTERWAVE_API_KEY", default=""),
    "SECRET_HASH": config("FLUTTERWAVE_SECRET_HASH", default=""),
    "USE_SANDBOX": config("FLUTTERWAVE_USE_SANDBOX", cast=bool, default=True),
    "ALLOWED_IPS": ["52.31.139.75/32", "52.49.173.169/32"],
}

# Stripe
STRIPE = {
    "SECRET_KEY": config("STRIPE_SECRET_KEY", default=""),
    "PUBLISHABLE_KEY": config("STRIPE_PUBLISHABLE_KEY", default=""),
    "WEBHOOK_SECRET": config("STRIPE_WEBHOOK_SECRET", default=""),
    "ALLOWED_IPS": ["3.18.12.63/32", "3.130.192.231/32", "13.235.14.237/32"],
}


# ===========================
# Elasticsearch Configuration
# ===========================
ELASTICSEARCH_ENABLED = config("ELASTICSEARCH_ENABLED", default=False, cast=bool)
ELASTICSEARCH_HOST = config('ELASTICSEARCH_HOST', default='localhost:9200')

if DEBUG or not ELASTICSEARCH_ENABLED:
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ['localhost:9200']
        }
    }
    ELASTICSEARCH_DSL_AUTOSYNC = False
    ELASTICSEARCH_DSL_AUTO_REFRESH = False
    logger.info("Elasticsearch DISABLED (development mode)")
else:
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ELASTICSEARCH_HOST
        }
    }
    ELASTICSEARCH_DSL_AUTOSYNC = True
    ELASTICSEARCH_DSL_AUTO_REFRESH = True
    logger.info("Elasticsearch ENABLED (production mode)")


# ===========================
# Security Configuration
# ===========================
SECURITY_2FA_PROTECTED_PATHS = [
    r"^/api/v1/payments/.*$",
    r"^/api/v1/businesses/.*/settings/?$",
]

SECURITY_OTP_TOKEN_MAX_AGE = 60 * 15   # 15 minutes
SECURITY_OTP_SIGNING_SALT = "y_oYMBD_QTQDBRVrAMA9syhkVTtDCdKi9--si7Abm54"
SECURITY_OTP_SESSION_TTL_SECONDS = 60 * 15
SECURITY_OTP_REQUEST_LIMIT = 5
SECURITY_OTP_REQUEST_WINDOW = 60 * 60
SECURITY_OTP_REQUEST_COOLDOWN = 10
SECURITY_OTP_REQUEST_URL = "/api/v1/security/otp/request/"

# High Value Payment Thresholds (for OTP verification)
SECURITY_HIGH_VALUE_PAYMENT_THRESHOLD = {
    "TZS": 10_000,
    "KES": 5_000,
    "UGX": 100_000,
    "USD": 10,
    "EUR": 10,
}


# ===========================
# Payment System Configuration
# ===========================
PAYMENT_SYSTEM = {
    "MAX_BULK_PAYMENTS_PER_EXECUTION": 1000,
    "SCHEDULED_PAYMENT_ADVANCE_NOTICE_HOURS": 24,
    "PAYMENT_LINK_EXPIRY_DAYS": 7,
    "REPORT_RETENTION_DAYS": 30,
    "AUTO_RETRY_FAILED_PAYMENTS": True,
    "MAX_PAYMENT_RETRIES": 5,
}

# Payment Link Settings
PAYMENT_LINK = {
    "DEFAULT_EXPIRY_DAYS": 7,
    "ALLOWED_METHODS": ["WALLET", "PAWAPAY", "CREDIT_CARD"],
    "MAX_AMOUNT": {
        "TZS": 1_000_000,
        "KES": 500_000,
        "USD": 1000,
    }
}

# Bulk Payment Settings
BULK_PAYMENT = {
    "MAX_PAYMENTS_PER_BATCH": 1000,
    "MAX_TOTAL_AMOUNT_PER_BATCH": {
        "TZS": 10_000_000,
        "KES": 5_000_000,
        "USD": 10_000,
    },
    "ALLOWED_CURRENCIES": ["TZS", "KES", "UGX", "USD"],
}

# Scheduled Payment Settings
SCHEDULED_PAYMENT = {
    "MAX_FUTURE_DAYS": 365,
    "ADVANCE_NOTICE_HOURS": 24,
    "AUTO_CANCEL_FAILED_AFTER_DAYS": 7,
}


# ===========================
# Sentry (Error Tracking)
# ===========================
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )


# ===========================
# Logging Configuration
# ===========================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{"
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/debug.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO" if not DEBUG else "DEBUG",
            "propagate": True,
        },
        "pawapay": {
            "handlers": ["console", "file"],
            "level": "INFO" if not DEBUG else "DEBUG",
            "propagate": True,
        },
        "jamiikazini": {
            "handlers": ["console", "file"],
            "level": "INFO" if not DEBUG else "DEBUG",
            "propagate": True,
        },
    },
}


