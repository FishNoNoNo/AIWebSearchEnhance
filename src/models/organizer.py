from __future__ import annotations

from src.search.models import SearchResult


class SearchResultOrganizer:
    def __init__(self) -> None:
        pass

    async def organize(self, results: list[SearchResult]) -> str:
        if not results:
            return "## 搜索结果摘要\n未找到可用搜索结果。"
        return self._fallback_markdown(results)

    def _fallback_markdown(self, results: list[SearchResult]) -> str:
        lines = ["## 搜索结果摘要"]
        seen: set[str] = set()
        index = 1
        for item in results:
            key = item.link or item.title
            if key in seen:
                continue
            seen.add(key)
            lines.extend(
                [
                    f"{index}. **[{item.title}]** (来源：{item.source or item.engine})",
                    f"   - 摘要：{item.snippet or '无摘要'}",
                    f"   - 链接：{item.link}",
                ]
            )
            index += 1
        return "\n".join(lines)
