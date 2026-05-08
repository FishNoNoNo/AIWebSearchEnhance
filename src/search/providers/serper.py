from __future__ import annotations

from urllib.parse import urlparse

import httpx

from src.core.exceptions import SearchEngineError
from src.search.base import SearchEngineBase
from src.search.models import SearchResult


class SerperSearch(SearchEngineBase):
    name = "serper"
    required_config_keys = ("api_key",)

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        self.ensure_configured()
        endpoint = self.config.get("endpoint") or "https://google.serper.dev/search"
        headers = {"X-API-KEY": self.config["api_key"], "Content-Type": "application/json"}
        payload = {"q": query, "num": max_results}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise SearchEngineError("Serper search failed", details=str(exc)) from exc
        results: list[SearchResult] = []
        for item in data.get("organic", []):
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
