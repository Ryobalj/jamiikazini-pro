# jamiiwallet/services/cache_utils.py

import logging
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Optional: use django-redis for advanced operations (locks)
try:
    from django_redis import get_redis_connection
    _HAS_DJANGO_REDIS = True
except Exception:
    _HAS_DJANGO_REDIS = False
    get_redis_connection = None  # type: ignore

# Configurable defaults
_BALANCE_TTL = getattr(settings, "WALLET_BALANCE_CACHE_TTL", 300)  # seconds (5m)
_USER_TTL = getattr(settings, "USER_CACHE_TTL", 600)  # seconds (10m)
_LOCK_TIMEOUT = getattr(settings, "WALLET_CACHE_LOCK_TIMEOUT", 5)  # seconds


def _balance_key(user_id: str) -> str:
    return f"wallet:balance:{user_id}"


def _user_by_email_key(email: str) -> str:
    return f"user:by_email:{email.lower()}"


def _user_by_phone_key(phone: str) -> str:
    return f"user:by_phone:{phone}"


# --- Wallet balance cache --- #
def get_cached_balance(user_id):
    key = _balance_key(user_id)
    val = cache.get(key)
    if val is None:
        logger.debug("[cache] miss balance %s", user_id)
        return None
    try:
        # stored as string
        return Decimal(val)
    except Exception:
        logger.exception("Failed to parse cached balance for %s: %r", user_id, val)
        return None


def set_cached_balance(user_id, balance, ttl=_BALANCE_TTL):
    key = _balance_key(user_id)
    try:
        # store as plain string to avoid JSON/Decimal issues
        cache.set(key, str(balance), ttl)
        logger.debug("[cache] set balance %s -> %s (ttl=%s)", user_id, balance, ttl)
        return True
    except Exception:
        logger.exception("Failed to set cached balance for %s", user_id)
        return False


def invalidate_cached_balance(user_id):
    key = _balance_key(user_id)
    try:
        cache.delete(key)
        logger.debug("[cache] invalidated balance %s", user_id)
        return True
    except Exception:
        logger.exception("Failed to invalidate cached balance for %s", user_id)
        return False


def acquire_balance_lock(user_id):
    """
    Acquire a short-lived lock in Redis to coordinate cache updates.
    Returns a lock object (redis-py Lock) or None if redis not available.
    Caller must release() if lock acquired.
    """
    if not _HAS_DJANGO_REDIS:
        return None
    try:
        client = get_redis_connection("default")
        lock = client.lock(f"lock:wallet:balance:{user_id}", timeout=_LOCK_TIMEOUT)
        got = lock.acquire(blocking=True, blocking_timeout=1)
        if not got:
            logger.debug("[cache][lock] could not acquire lock for %s", user_id)
            return None
        logger.debug("[cache][lock] acquired for %s", user_id)
        return lock
    except Exception:
        logger.exception("[cache][lock] error acquiring lock for %s", user_id)
        return None


# --- User lookups caching (email/phone) --- #
def cache_user_lookup_by_email(email: str, user_id: str, ttl=_USER_TTL):
    key = _user_by_email_key(email)
    try:
        cache.set(key, str(user_id), ttl)
        logger.debug("[cache] set user_by_email %s -> %s", email, user_id)
        return True
    except Exception:
        logger.exception("Failed to cache user_by_email %s", email)
        return False


def get_cached_user_id_by_email(email: str):
    key = _user_by_email_key(email)
    val = cache.get(key)
    if val:
        logger.debug("[cache] hit user_by_email %s -> %s", email, val)
    else:
        logger.debug("[cache] miss user_by_email %s", email)
    return val


def cache_user_lookup_by_phone(phone: str, user_id: str, ttl=_USER_TTL):
    key = _user_by_phone_key(phone)
    try:
        cache.set(key, str(user_id), ttl)
        logger.debug("[cache] set user_by_phone %s -> %s", phone, user_id)
        return True
    except Exception:
        logger.exception("Failed to cache user_by_phone %s", phone)
        return False


def get_cached_user_id_by_phone(phone: str):
    key = _user_by_phone_key(phone)
    val = cache.get(key)
    if val:
        logger.debug("[cache] hit user_by_phone %s -> %s", phone, val)
    else:
        logger.debug("[cache] miss user_by_phone %s", phone)
    return val