from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is optional at import time
    load_dotenv = None

from src.core.exceptions import InvalidRequestError


ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")
DEFAULT_CONFIG_PATH = Path("config/config.yaml")


class ModelSettings(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout: float = 30
    max_retries: int = 3
    organization: str | None = None
    default_headers: dict[str, str] = Field(default_factory=dict)
    api_version: str | None = None


class SearchEngineSettings(BaseModel):
    name: str
    enabled: bool = True
    priority: int = 100
    config: dict[str, Any] = Field(default_factory=dict)


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 18080
    workers: int = 1
    request_timeout: int = 120


class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: str = "json"
    output: str = "stdout"


class RedisSettings(BaseModel):
    enabled: bool = False
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    max_connections: int = 50
    socket_timeout: float = 5
    socket_connect_timeout: float = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class CacheSettings(BaseModel):
    enabled: bool = True
    ttl: int = 3600
    max_size: int = 1000
    backend: str = "memory"

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, value: str) -> str:
        if value not in {"memory", "redis"}:
            raise ValueError("cache.backend must be memory or redis")
        return value


class SearchStrategySettings(BaseModel):
    min_confidence_threshold: float = 0.6
    max_search_queries: int = 3
    result_per_query: int = 5


class AppConfig(BaseModel):
    analysis_model: ModelSettings = Field(default_factory=ModelSettings)
    search_engines: list[SearchEngineSettings] = Field(default_factory=list)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    search_strategy: SearchStrategySettings = Field(default_factory=SearchStrategySettings)


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), m.group(2) or ""), value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def _load_dotenv() -> None:
    if load_dotenv is not None:
        load_dotenv(override=False)


def load_config(path: str | os.PathLike[str] | None = None) -> AppConfig:
    _load_dotenv()
    config_path = Path(path or os.getenv("AI_WEB_SEARCH_CONFIG", DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        raise InvalidRequestError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        raw_data = yaml.safe_load(file) or {}
    data = _expand_env(raw_data)
    config = AppConfig.model_validate(data)
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if config.server.port <= 0 or config.server.port > 65535:
        raise InvalidRequestError("server.port must be between 1 and 65535")
    if config.search_strategy.max_search_queries <= 0:
        raise InvalidRequestError("search_strategy.max_search_queries must be positive")
    if config.search_strategy.result_per_query <= 0:
        raise InvalidRequestError("search_strategy.result_per_query must be positive")
    if config.analysis_model.provider not in {"openai", "azure", "anthropic", "local"}:
        raise InvalidRequestError(
            f"Unsupported model provider: {config.analysis_model.provider}"
        )
    if config.analysis_model.timeout <= 0:
        raise InvalidRequestError("model timeout must be positive")
    seen_names: set[str] = set()
    for engine in config.search_engines:
        if engine.name in seen_names:
            raise InvalidRequestError(f"Duplicate search engine name: {engine.name}")
        seen_names.add(engine.name)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return load_config()
