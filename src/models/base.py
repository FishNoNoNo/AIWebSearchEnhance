from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from pydantic import BaseModel, Field


class ModelClientConfig(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str | None = "gpt-4o-mini"
    timeout: float = 30
    max_retries: int = 3
    organization: str | None = None
    default_headers: dict[str, str] = Field(default_factory=dict)
    api_version: str | None = None


class ModelGeneration(BaseModel):
    content: str
    raw: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)


class BaseModelClient(ABC):
    def __init__(self, config: ModelClientConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(
        self,
        messages: list[Mapping[str, Any]],
        *,
        model: str | None = None,
        **params: Any,
    ) -> ModelGeneration:
        raise NotImplementedError
