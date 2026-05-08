from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.core.exceptions import SearchEngineError
from src.search.models import SearchResult


class SearchEngineBase(ABC):
    name = "base"
    required_config_keys: tuple[str, ...] = ()

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        raise NotImplementedError

    def default_max_results(self) -> int:
        return int(self.config.get("max_results") or 5)

    def is_configured(self) -> bool:
        return all(bool(self.config.get(key)) for key in self.required_config_keys)

    async def health_check(self) -> bool:
        return self.is_configured()

    def ensure_configured(self) -> None:
        missing = [key for key in self.required_config_keys if not self.config.get(key)]
        if missing:
            raise SearchEngineError(
                f"Search engine {self.name} is missing required config: {', '.join(missing)}"
            )
