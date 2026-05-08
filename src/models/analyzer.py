from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from src.core.config_loader import ModelSettings
from src.models.base import BaseModelClient
from src.models.factories import ModelFactory

ANALYSIS_PROMPT = """你是一个搜索判断专家。分析以下用户输入，判断是否需要通过联网搜索来获取辅助信息。

判断原则：
- 需要搜索的情况：实时动态信息、最新状态、事实核验、特定地点/时间相关信息、用户明确要求搜索、专业领域最新进展、你无法确定或记忆模糊的信息。
- 不需要搜索的情况：通用常识、数学计算、逻辑推理、代码编写、技术原理、创意写作、翻译润色、情感建议，或用户明确要求不用搜索。

只输出 JSON：
{{
  "need_search": true,
  "confidence": 0.0,
  "search_queries": ["query1","query2"],
  "reason": "判断理由"
}}

用户输入：{user_message}
"""


class SearchAnalysis(BaseModel):
    need_search: bool
    confidence: float = Field(ge=0, le=1)
    search_queries: list[str] = Field(default_factory=list)
    reason: str = ""


class SearchAnalyzer:
    def __init__(
        self,
        settings: ModelSettings,
        *,
        client: BaseModelClient | None = None,
        factory: ModelFactory | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or (factory or ModelFactory()).create_from_settings(
            settings
        )

    async def analyze(self, user_message: str) -> SearchAnalysis:
        if not self.settings.api_key:
            return self._heuristic(user_message)
        try:
            generation = await self.client.generate(
                [
                    {
                        "role": "user",
                        "content": ANALYSIS_PROMPT.format(user_message=user_message),
                    }
                ],
                model=self.settings.model,
            )
            return self._parse_generation(generation.content, user_message)
        except Exception as e:
            print(e)
            return self._heuristic(user_message)

    def _parse_generation(self, content: str, user_message: str) -> SearchAnalysis:
        text = content.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if fenced:
            text = fenced.group(1).strip()
        try:
            data: dict[str, Any] = json.loads(text)
            analysis = SearchAnalysis.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            return self._heuristic(user_message)
        if analysis.need_search and not analysis.search_queries:
            analysis.search_queries = [self._normalize_query(user_message)]
        return analysis

    def _heuristic(self, user_message: str) -> SearchAnalysis:
        lowered = user_message.lower()
        no_search_markers = [
            "不用搜索",
            "不要搜索",
            "无需联网",
            "直接回答",
            "no search",
            "without searching",
        ]
        if any(marker in lowered for marker in no_search_markers):
            return SearchAnalysis(
                need_search=False,
                confidence=0.92,
                search_queries=[],
                reason="用户明确要求不搜索",
            )
        search_markers = [
            "今天",
            "昨日",
            "昨天",
            "明天",
            "现在",
            "目前",
            "最新",
            "近期",
            "新闻",
            "天气",
            "股价",
            "价格",
            "汇率",
            "赛事",
            "赛程",
            "查一下",
            "搜索",
            "联网",
            "current",
            "latest",
            "today",
            "weather",
            "news",
            "price",
            "stock",
        ]
        need_search = any(marker in lowered for marker in search_markers)
        confidence = 0.78 if need_search else 0.68
        return SearchAnalysis(
            need_search=need_search,
            confidence=confidence,
            search_queries=[self._normalize_query(user_message)] if need_search else [],
            reason="基于关键词启发式判断" if need_search else "未发现明显实时信息需求",
        )

    def _normalize_query(self, value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        return value[:120]
