import pytest
from django.core.cache import cache
from redis.exceptions import ConnectionError

@pytest.mark.django_db
def test_redis_cache_connection():
    try:
        # Set a test key in cache
        cache.set('test_redis_key', 'working', timeout=5)
        value = cache.get('test_redis_key')

        assert value == 'working', "Redis cache is not working properly"
        print("✅ Redis connection and caching successful")

    except ConnectionError:
        pytest.fail("❌ Cannot connect to Redis server. Is Redis running?")