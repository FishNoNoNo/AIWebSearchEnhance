from __future__ import annotations

import asyncio
from typing import Any, Mapping

import httpx

from src.core.exceptions import ModelUnavailableError
from src.models.base import BaseModelClient, ModelGeneration


class OpenAIClient(BaseModelClient):
    async def generate(
        self,
        messages: list[Mapping[str, Any]],
        *,
        model: str | None = None,
        **params: Any,
    ) -> ModelGeneration:
        if not self.config.api_key:
            raise ModelUnavailableError("Model api_key is missing")
        payload = {
            "model": model or self.config.model,
            "messages": list(messages),
            "stream": False,
        }
        payload.update({key: value for key, value in params.items() if value is not None})
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            **self.config.default_headers,
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        data = await self._post_json(url, payload, headers)
        message = (data.get("choices") or [{}])[0].get("message") or {}
        return ModelGeneration(
            content=message.get("content") or "",
            raw=data,
            usage=data.get("usage") or {},
        )

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
                        f"Model request failed with status {response.status_code}",
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
        raise ModelUnavailableError("Model request failed", details=str(last_error))
