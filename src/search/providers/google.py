from __future__ import annotations

from urllib.parse import urlparse

import httpx

from src.core.exceptions import SearchEngineError
from src.search.base import SearchEngineBase
from src.search.models import SearchResult


class GoogleSearch(SearchEngineBase):
    name = "google"
    required_config_keys = ("api_key", "search_engine_id")

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        self.ensure_configured()
        endpoint = self.config.get("endpoint") or "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.config["api_key"],
            "cx": self.config["search_engine_id"],
            "q": query,
            "num": min(max_results, 10),
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise SearchEngineError("Google search failed", details=str(exc)) from exc
        results: list[SearchResult] = []
        for item in data.get("items", []):
            link = item.get("link") or ""
            results.append(
                SearchResult(
                    title=item.get("title") or link,
                    link=link,
                    snippet=item.get("snippet") or "",
                    source=urlparse(link).netloc,
                    engine=self.name,
                )
            )
        return results
