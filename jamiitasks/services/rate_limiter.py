# jamiitasks/services/rate_limiter.py

import time
import redis
from django.conf import settings

class TaskRateLimiter:
    def __init__(self, prefix="celery_rate", limit=10, period=60):
        """
        limit = idadi ya task zinazoruhusiwa ndani ya 'period' sekunde
        """
        self.prefix = prefix
        self.limit = limit
        self.period = period
        self.redis = redis.Redis.from_url(settings.CELERY_BROKER_URL)

    def allow(self, task_name):
        key = f"{self.prefix}:{task_name}"
        now = int(time.time())
        pipe = self.redis.pipeline()

        # tunahifadhi timestamps kwenye sorted set
        pipe.zremrangebyscore(key, 0, now - self.period)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.period)
        results = pipe.execute()

        count = results[2]  # idadi ya entries baada ya kusafisha
        return count <= self.limit