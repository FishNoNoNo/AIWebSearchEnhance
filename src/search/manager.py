from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from src.cache.base import BaseCache
from src.cache.decorator import CacheKeyGenerator
from src.core.config_loader import SearchEngineSettings
from src.core.exceptions import SearchEngineError
from src.search.base import SearchEngineBase
from src.search.models import SearchResponseData, SearchResult
from src.search.providers.baidu import BaiduSearch
from src.search.providers.bing import BingSearch
from src.search.providers.google import GoogleSearch
from src.search.providers.searxng import SearxngSearch
from src.search.providers.serper import SerperSearch
from src.utils.metrics import MetricsCollector


PROVIDERS: dict[str, type[SearchEngineBase]] = {
    "google": GoogleSearch,
    "bing": BingSearch,
    "serper": SerperSearch,
    "baidu": BaiduSearch,
    "searxng": SearxngSearch,
}


@dataclass(slots=True)
class ManagedSearchEngine:
    engine: SearchEngineBase
    enabled: bool
    priority: int
    failure_count: int = 0
    circuit_open_until: float = 0
    last_latency_ms: float | None = None
    last_error: str | None = None


class SearchEngineManager:
    def __init__(
        self,
        engines: list[ManagedSearchEngine],
        *,
        cache: BaseCache | None = None,
        cache_ttl: int = 3600,
        metrics: MetricsCollector | None = None,
        circuit_threshold: int = 3,
        circuit_cooldown_seconds: int = 60,
    ) -> None:
        self.engines = sorted(engines, key=lambda item: item.priority)
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.metrics = metrics
        self.circuit_threshold = circuit_threshold
        self.circuit_cooldown_seconds = circuit_cooldown_seconds

    @classmethod
    def from_settings(
        cls,
        settings: list[SearchEngineSettings],
        *,
        cache: BaseCache | None = None,
        cache_ttl: int = 3600,
        metrics: MetricsCollector | None = None,
    ) -> "SearchEngineManager":
        engines: list[ManagedSearchEngine] = []
        for item in settings:
            provider_cls = PROVIDERS.get(item.name)
            if provider_cls is None:
                continue
            engines.append(
                ManagedSearchEngine(
                    engine=provider_cls(item.config),
                    enabled=item.enabled,
                    priority=item.priority,
                )
            )
        return cls(engines, cache=cache, cache_ttl=cache_ttl, metrics=metrics)

    def get_available_engines(self, requested: str = "auto") -> list[ManagedSearchEngine]:
        now = monotonic()
        candidates = [
            item
            for item in self.engines
            if item.enabled and (requested == "auto" or item.engine.name == requested)
        ]
        return [item for item in candidates if item.circuit_open_until <= now]

    async def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        engine: str = "auto",
    ) -> SearchResponseData:
        candidates = self.get_available_engines(engine)
        if not candidates:
            raise SearchEngineError("No available search engines")
        errors: dict[str, str] = {}
        for managed in candidates:
            limit = max_results or managed.engine.default_max_results()
            cache_key = CacheKeyGenerator.search(managed.engine.name, query, limit)
            cached = await self._cache_get(cache_key)
            if cached is not None:
                results = [SearchResult.model_validate(item) for item in cached]
                return SearchResponseData(
                    query=query,
                    engine_used=managed.engine.name,
                    results=results,
                    total_results=len(results),
                )
            started = monotonic()
            try:
                results = await managed.engine.search(query, max_results=limit)
                managed.failure_count = 0
                managed.last_error = None
                managed.last_latency_ms = round((monotonic() - started) * 1000, 2)
                await self._cache_set(
                    cache_key, [item.model_dump(mode="json") for item in results]
                )
                if self.metrics:
                    self.metrics.record_engine_usage(managed.engine.name)
                return SearchResponseData(
                    query=query,
                    engine_used=managed.engine.name,
                    results=results,
                    total_results=len(results),
                )
            except Exception as exc:
                self._record_failure(managed, exc)
                errors[managed.engine.name] = str(exc)
        raise SearchEngineError("All search engines failed", details=errors)

    async def health_check(self) -> dict[str, dict[str, object]]:
        checks: dict[str, dict[str, object]] = {}
        for managed in self.engines:
            ok = managed.enabled and await managed.engine.health_check()
            available = ok and managed.circuit_open_until <= monotonic()
            checks[managed.engine.name] = {
                "enabled": managed.enabled,
                "available": available,
                "priority": managed.priority,
                "latency_ms": managed.last_latency_ms,
                "failure_count": managed.failure_count,
                "last_error": managed.last_error,
            }
        return checks

    def _record_failure(self, managed: ManagedSearchEngine, exc: Exception) -> None:
        managed.failure_count += 1
        managed.last_error = str(exc)
        if managed.failure_count >= self.circuit_threshold:
            managed.circuit_open_until = monotonic() + self.circuit_cooldown_seconds

    async def _cache_get(self, key: str) -> object | None:
        if self.cache is None:
            return None
        value = await self.cache.get(key)
        if self.metrics:
            if value is None:
                self.metrics.record_cache_miss()
            else:
                self.metrics.record_cache_hit()
        return value

    async def _cache_set(self, key: str, value: object) -> None:
        if self.cache is not None:
            await self.cache.set(key, value, ttl=self.cache_ttl)
