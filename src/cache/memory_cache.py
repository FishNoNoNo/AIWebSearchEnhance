from __future__ import annotations

from time import time
from typing import Any

from src.cache.base import BaseCache


class MemoryCache(BaseCache):
    def __init__(self, *, ttl: int = 3600, max_size: int = 1000, enabled: bool = True) -> None:
        self.ttl = ttl
        self.max_size = max_size
        self.enabled = enabled
        self._store: dict[str, tuple[float, Any]] = {}

    async def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time():
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self.enabled:
            return
        if len(self._store) >= self.max_size:
            oldest_key = min(self._store, key=lambda item: self._store[item][0])
            self._store.pop(oldest_key, None)
        self._store[key] = (time() + (ttl or self.ttl), value)

    async def delete_pattern(self, pattern: str) -> int:
        if pattern == "*":
            count = len(self._store)
            self._store.clear()
            return count
        prefix = pattern.rstrip("*")
        keys = [key for key in self._store if key.startswith(prefix)]
        for key in keys:
            self._store.pop(key, None)
        return len(keys)

    async def health_check(self) -> bool:
        return True
