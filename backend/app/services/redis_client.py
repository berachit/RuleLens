import time
import logging
from typing import Optional, Tuple, Any
import redis
from app.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Manages Redis connection with graceful degradation when Redis is offline."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._is_connected: bool = False
        self._in_memory_fallback: dict = {}

    def get_client(self) -> Optional[redis.Redis]:
        if not settings.REDIS_ENABLED:
            return None

        if self._client is None:
            try:
                self._client = redis.from_url(
                    settings.REDIS_URL,
                    socket_timeout=settings.REDIS_TIMEOUT_SECONDS,
                    socket_connect_timeout=settings.REDIS_TIMEOUT_SECONDS,
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning(f"Could not initialize Redis client: {e}")
                self._client = None
        return self._client

    def ping(self) -> Tuple[bool, float, Optional[str]]:
        """Pings Redis to determine connectivity and round-trip latency."""
        if not settings.REDIS_ENABLED:
            return False, 0.0, "Redis is disabled by configuration"

        client = self.get_client()
        if client is None:
            return False, 0.0, "Redis client could not be instantiated"

        start_time = time.time()
        try:
            client.ping()
            latency_ms = round((time.time() - start_time) * 1000, 2)
            self._is_connected = True
            return True, latency_ms, None
        except Exception as exc:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            self._is_connected = False
            return False, latency_ms, str(exc)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Safely stores a key-value pair, falling back to memory if Redis is down."""
        client = self.get_client()
        if client:
            try:
                client.set(key, value, ex=ex)
                return True
            except Exception as e:
                logger.debug(f"Redis set failed, falling back to memory: {e}")

        self._in_memory_fallback[key] = value
        return True

    def get(self, key: str) -> Optional[str]:
        """Safely retrieves a value by key, falling back to memory if Redis is down."""
        client = self.get_client()
        if client:
            try:
                val = client.get(key)
                if val is not None:
                    return val
            except Exception as e:
                logger.debug(f"Redis get failed, falling back to memory: {e}")

        return self._in_memory_fallback.get(key)


redis_manager = RedisManager()
