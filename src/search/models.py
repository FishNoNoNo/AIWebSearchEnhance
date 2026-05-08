from __future__ import annotations

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str = ""
    source: str = ""
    engine: str = ""
    published_at: str | None = None


class SearchResponseData(BaseModel):
    query: str
    engine_used: str
    results: list[SearchResult] = Field(default_factory=list)
    total_results: int = 0
