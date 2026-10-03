from collections import defaultdict
from threading import Lock
from time import monotonic

import redis

from app.config import get_settings


class ResilientCache:
    """Redis-backed cache with a safe in-process fallback for local development."""

    def __init__(self) -> None:
        self._redis = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
        self._fallback: dict[str, tuple[str, float]] = {}
        self._counters: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self._lock = Lock()

    def _redis_available(self) -> bool:
        try:
            return bool(self._redis.ping())
        except redis.RedisError:
            return False

    def get(self, key: str) -> str | None:
        if self._redis_available():
            return self._redis.get(key)
        with self._lock:
            value = self._fallback.get(key)
            if not value or value[1] < monotonic():
                self._fallback.pop(key, None)
                return None
            return value[0]

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if self._redis_available():
            self._redis.setex(key, ttl_seconds, value)
            return
        with self._lock:
            self._fallback[key] = (value, monotonic() + ttl_seconds)

    def increment(self, key: str, ttl_seconds: int) -> int:
        if self._redis_available():
            pipe = self._redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl_seconds)
            return int(pipe.execute()[0])
        with self._lock:
            count, expires_at = self._counters[key]
            if expires_at < monotonic():
                count = 0
                expires_at = monotonic() + ttl_seconds
            count += 1
            self._counters[key] = (count, expires_at)
            return count
