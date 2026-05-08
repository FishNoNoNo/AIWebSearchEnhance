from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.search.models import SearchResult


class ClientInitResponse(BaseModel):
    success: bool = True
    client_id: str
    message: str = "Client initialized successfully"


class SearchMetadata(BaseModel):
    searched: bool
    search_queries: list[str] = Field(default_factory=list)
    engine_used: str | None = None
    result_count: int = 0
    sources: list[dict[str, str]] = Field(default_factory=list)
    reason: str = ""


class SearchOnlyResponse(BaseModel):
    query: str
    engine_used: str
    results: list[SearchResult]
    total_results: int


class ClearCacheResponse(BaseModel):
    success: bool = True
    cleared_count: int


class ErrorResponse(BaseModel):
    error: dict[str, Any]
