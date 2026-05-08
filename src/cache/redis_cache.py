from __future__ import annotations

import json
from typing import Any

from src.cache.base import BaseCache
from src.core.config_loader import RedisSettings

try:
    import redis.asyncio as redis
except ImportError:  # pragma: no cover - optional dependency
    redis = None


class RedisCache(BaseCache):
    def __init__(self, settings: RedisSettings, *, namespace: str = "ai-web-search") -> None:
        if redis is None:
            raise RuntimeError("redis package is not installed")
        self.namespace = namespace
        self.client = redis.Redis(
            host=settings.host,
            port=settings.port,
            password=settings.password or None,
            db=settings.db,
            max_connections=settings.max_connections,
            socket_timeout=settings.socket_timeout,
            socket_connect_timeout=settings.socket_connect_timeout,
            retry_on_timeout=settings.retry_on_timeout,
            health_check_interval=settings.health_check_interval,
            decode_responses=True,
        )

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Any | None:
        value = await self.client.get(self._key(key))
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.client.set(self._key(key), json.dumps(value, ensure_ascii=False), ex=ttl)

    async def delete_pattern(self, pattern: str) -> int:
        redis_pattern = self._key(pattern)
        count = 0
        async for key in self.client.scan_iter(match=redis_pattern):
            count += await self.client.delete(key)
        return count

    async def health_check(self) -> bool:
        try:
            return bool(await self.client.ping())
        except Exception:
            return False
