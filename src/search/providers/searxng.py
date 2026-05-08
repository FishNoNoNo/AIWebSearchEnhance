from __future__ import annotations

from urllib.parse import urlparse

import httpx

from src.core.exceptions import SearchEngineError
from src.search.base import SearchEngineBase
from src.search.models import SearchResult


class SearxngSearch(SearchEngineBase):
    name = "searxng"
    required_config_keys = ("endpoint",)

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        self.ensure_configured()
        endpoint = self.config.get("endpoint")
        # categories=general; language=auto; locale=zh-Hans-CN; autocomplete=; favicon_resolver=; image_proxy=0; safesearch=0; theme=simple; results_on_new_tab=0; doi_resolver=oadoi.org; simple_style=auto; center_alignment=0; advanced_search=0; query_in_title=0; search_on_category_select=1; hotkeys=default; url_formatting=pretty; disabled_engines="wikipedia__general\054currency__general\054wikidata__general\054duckduckgo__general\054google__general\054karmasearch__general\054lingva__general\054startpage__general\054dictzone__general\054mymemory translated__general\054brave__general"; enabled_engines=bing__general; disabled_plugins=; enabled_plugins=; tokens=; method=GET
        cookies = {
            "categories": "general",
            "language": "auto",
            "locale": "zh-Hans-CN",
            "autocomplete": "",
            "favicon_resolver": "",
            "image_proxy": "0",
            "safesearch": "0",
            "theme": "simple",
            "results_on_new_tab": "0",
            "doi_resolver": "oadoi.org",
            "simple_style": "auto",
            "center_alignment": "0",
            "advanced_search": "0",
            "query_in_title": "0",
            "search_on_category_select": "1",
            "hotkeys": "default",
            "url_formatting": "pretty",
            "disabled_engines": '"wikipedia__general\\054currency__general\\054wikidata__general\\054duckduckgo__general\\054google__general\\054karmasearch__general\\054lingva__general\\054startpage__general\\054dictzone__general\\054mymemory translated__general\\054brave__general"',
            "disabled_plugins": "",
            "enabled_plugins": "",
            "tokens": "",
            "method": "GET",
            "enabled_engines": '"bing__general\\054sogou__general"',
        }
        # http://127.0.0.1:12080/search?q=searxng&category_general=1&pageno=1&language=auto&time_range=&safesearch=0&format=json

        params = {
            "q": query,
            "category_general": 1,
            "pageno": 1,
            "language": "auto",
            "time_range": "",
            "safesearch": 0,
            "format": "json",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(endpoint, params=params, cookies=cookies)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise SearchEngineError("Bing search failed", details=str(exc)) from exc
        values = data.get("results") or []
        results: list[SearchResult] = []
        for item in values[:3]:
            link = item.get("url") or ""
            results.append(
                SearchResult(
                    title=item.get("title") or link,
                    link=link,
                    snippet=item.get("content") or "",
                    source=urlparse(link).netloc,
                    engine=item.get("engine"),
                )
            )
        return results
