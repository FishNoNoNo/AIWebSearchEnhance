from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
