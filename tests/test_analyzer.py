from __future__ import annotations

import pytest

from src.core.config_loader import ModelSettings
from src.models.analyzer import SearchAnalyzer


@pytest.mark.asyncio
async def test_analyzer_detects_realtime_question() -> None:
    analyzer = SearchAnalyzer(ModelSettings(api_key=""))
    result = await analyzer.analyze("今天北京天气怎么样？")
    assert result.need_search is True
    assert result.search_queries


@pytest.mark.asyncio
async def test_analyzer_respects_no_search_instruction() -> None:
    analyzer = SearchAnalyzer(ModelSettings(api_key=""))
    result = await analyzer.analyze("不用搜索，解释一下二分查找")
    assert result.need_search is False
    assert result.confidence > 0.9
