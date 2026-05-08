from __future__ import annotations

from src.core.config_loader import ModelSettings
from src.core.exceptions import InvalidRequestError
from src.models.base import BaseModelClient, ModelClientConfig
from src.models.clients.anthropic_client import AnthropicClient
from src.models.clients.azure_client import AzureClient
from src.models.clients.openai_client import OpenAIClient


class ModelFactory:
    def create(self, config: ModelClientConfig) -> BaseModelClient:
        provider = config.provider.lower()
        if provider in {"openai", "local"}:
            return OpenAIClient(config)
        if provider == "azure":
            return AzureClient(config)
        if provider == "anthropic":
            return AnthropicClient(config)
        raise InvalidRequestError(f"Unsupported model provider: {config.provider}")

    def create_from_settings(self, settings: ModelSettings) -> BaseModelClient:
        return self.create(
            ModelClientConfig(
                provider=settings.provider,
                api_key=settings.api_key,
                base_url=settings.base_url,
                model=settings.model,
                timeout=settings.timeout,
                max_retries=settings.max_retries,
                organization=settings.organization,
                default_headers=settings.default_headers,
                api_version=settings.api_version,
            )
        )
