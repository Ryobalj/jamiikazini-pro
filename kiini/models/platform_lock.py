# kiini/models/platform_lock.py

from types import SimpleNamespace

from django.core.cache import cache
from django.db import models

CACHE_KEY = "platform_lock:singleton"
CACHE_TTL_SECONDS = 30


class PlatformLock(models.Model):
    """
    Single-row switch for locking the whole platform down to the JamiiShule
    module only (e.g. while finishing government-linking API requirements).
    Always read via PlatformLock.load() - never query this model directly -
    so every request doesn't hit the DB for a value that changes maybe once
    a year.
    """
    is_locked = models.BooleanField(default=False)
    message = models.TextField(
        blank=True,
        help_text="Shown to locked-out users. Leave blank to use the default notice.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform lock"
        verbose_name_plural = "Platform lock"

    def __str__(self):
        return "Locked" if self.is_locked else "Unlocked"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(CACHE_KEY)

    @classmethod
    def load(cls):
        """
        Returns a lightweight (is_locked, message) view, cached as a plain
        dict rather than the model instance - the default cache backend in
        production is Redis with a JSON serializer, which can't pickle a
        Django model instance.
        """
        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return SimpleNamespace(**cached)
        obj, _ = cls.objects.get_or_create(pk=1)
        data = {"is_locked": obj.is_locked, "message": obj.message}
        cache.set(CACHE_KEY, data, CACHE_TTL_SECONDS)
        return SimpleNamespace(**data)
