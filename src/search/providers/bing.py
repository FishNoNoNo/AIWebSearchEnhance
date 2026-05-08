from __future__ import annotations

from urllib.parse import urlparse

import httpx

from src.core.exceptions import SearchEngineError
from src.search.base import SearchEngineBase
from src.search.models import SearchResult


class BingSearch(SearchEngineBase):
    name = "bing"
    required_config_keys = ("api_key",)

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        self.ensure_configured()
        endpoint = self.config.get("endpoint") or "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.config["api_key"]}
        params = {"q": query, "count": max_results}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise SearchEngineError("Bing search failed", details=str(exc)) from exc
        values = (data.get("webPages") or {}).get("value") or []
        results: list[SearchResult] = []
        for item in values:
            link = item.get("url") or ""
            results.append(
                SearchResult(
                    title=item.get("name") or link,
                    link=link,
                    snippet=item.get("snippet") or "",
                    source=urlparse(link).netloc,
                    engine=self.name,
                )
            )
        return results
