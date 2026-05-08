from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ClientInitRequest(BaseModel):
    provider: Literal["openai", "azure", "anthropic", "local"] = "openai"
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str | None = None
    organization: str | None = None
    timeout: float = 60
    default_headers: dict[str, str] | None = None
    api_version: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: Any
    name: str | None = None


class SearchOptions(BaseModel):
    force_search: bool = False
    disable_search: bool = False
    custom_queries: list[str] | None = None
    max_results: int | None = Field(default=None, ge=1, le=20)
    engine: str = "auto"


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    client_id: str | None = None
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    search_options: SearchOptions = Field(default_factory=SearchOptions)
    stream: bool = False

    def completion_params(self) -> dict[str, Any]:
        excluded = {"client_id", "messages", "model", "search_options", "stream"}
        return self.model_dump(exclude=excluded, exclude_none=True)


class SearchRequest(BaseModel):
    query: str
    client_id: str | None = None
    max_results: int = Field(default=5, ge=1, le=20)
    engine: str = "auto"


class ClearCacheRequest(BaseModel):
    pattern: str = "*"
