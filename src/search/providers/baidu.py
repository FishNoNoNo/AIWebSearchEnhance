from __future__ import annotations

from src.core.exceptions import SearchEngineError
from src.search.base import SearchEngineBase
from src.search.models import SearchResult


class BaiduSearch(SearchEngineBase):
    name = "baidu"
    required_config_keys = ("api_key", "secret")

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        self.ensure_configured()
        raise SearchEngineError(
            "Baidu search provider needs a concrete API product endpoint before it can be used"
        )
