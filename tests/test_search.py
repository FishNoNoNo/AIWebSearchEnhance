from __future__ import annotations

import pytest

from src.cache.memory_cache import MemoryCache
from src.search.base import SearchEngineBase
from src.search.manager import ManagedSearchEngine, SearchEngineManager
from src.search.models import SearchResult
from src.utils.metrics import MetricsCollector


class FakeSearch(SearchEngineBase):
    name = "fake"

    def __init__(self) -> None:
        super().__init__({})
        self.calls = 0

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        self.calls += 1
        return [
            SearchResult(
                title=f"Result for {query}",
                link="https://example.com/result",
                snippet="snippet",
                source="example.com",
                engine=self.name,
            )
        ]


@pytest.mark.asyncio
async def test_search_manager_uses_cache() -> None:
    engine = FakeSearch()
    manager = SearchEngineManager(
        [ManagedSearchEngine(engine=engine, enabled=True, priority=1)],
        cache=MemoryCache(ttl=60),
        metrics=MetricsCollector(),
    )
    first = await manager.search("hello", max_results=1)
    second = await manager.search("hello", max_results=1)
    assert first.results[0].title == second.results[0].title
    assert engine.calls == 1
