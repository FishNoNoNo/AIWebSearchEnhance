from __future__ import annotations

import asyncio
from typing import Any, Mapping

import httpx

from src.core.exceptions import ModelUnavailableError
from src.models.base import BaseModelClient, ModelGeneration


class AnthropicClient(BaseModelClient):
    async def generate(
        self,
        messages: list[Mapping[str, Any]],
        *,
        model: str | None = None,
        **params: Any,
    ) -> ModelGeneration:
        if not self.config.api_key:
            raise ModelUnavailableError("Model api_key is missing")
        system_parts: list[str] = []
        anthropic_messages: list[dict[str, Any]] = []
        for message in messages:
            role = str(message.get("role", "user"))
            content = message.get("content", "")
            if role == "system":
                system_parts.append(str(content))
            else:
                anthropic_messages.append(
                    {"role": "assistant" if role == "assistant" else "user", "content": content}
                )
        payload: dict[str, Any] = {
            "model": model or self.config.model,
            "messages": anthropic_messages,
            "max_tokens": params.pop("max_tokens", 1024),
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        payload.update({key: value for key, value in params.items() if value is not None})
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": self.config.api_version or "2023-06-01",
            "Content-Type": "application/json",
            **self.config.default_headers,
        }
        url = self.config.base_url.rstrip("/") + "/messages"
        data = await self._post_json(url, payload, headers)
        text = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
        return ModelGeneration(content=text, raw=data, usage=data.get("usage") or {})

    async def _post_json(
        self, url: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                if response.status_code >= 400:
                    raise ModelUnavailableError(
                        f"Anthropic request failed with status {response.status_code}",
                        details=response.text[:1000],
                    )
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError, ModelUnavailableError) as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                await asyncio.sleep(min(2**attempt, 8))
        if isinstance(last_error, ModelUnavailableError):
            raise last_error
        raise ModelUnavailableError("Anthropic request failed", details=str(last_error))
