from __future__ import annotations

from typing import Any, Mapping

from src.models.base import ModelGeneration
from src.models.clients.openai_client import OpenAIClient


class AzureClient(OpenAIClient):
    async def generate(
        self,
        messages: list[Mapping[str, Any]],
        *,
        model: str | None = None,
        **params: Any,
    ) -> ModelGeneration:
        deployment = model or self.config.model
        api_version = self.config.api_version or "2024-02-15-preview"
        payload = {"messages": list(messages), "stream": False}
        payload.update({key: value for key, value in params.items() if value is not None})
        headers = {
            "api-key": self.config.api_key,
            "Content-Type": "application/json",
            **self.config.default_headers,
        }
        url = (
            self.config.base_url.rstrip("/")
            + f"/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        )
        data = await self._post_json(url, payload, headers)
        message = (data.get("choices") or [{}])[0].get("message") or {}
        return ModelGeneration(
            content=message.get("content") or "",
            raw=data,
            usage=data.get("usage") or {},
        )
