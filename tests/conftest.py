from __future__ import annotations

import pytest

from src.core.config_loader import AppConfig, CacheSettings, LoggingSettings, RedisSettings


@pytest.fixture
def test_config() -> AppConfig:
    return AppConfig(
        search_engines=[],
        cache=CacheSettings(enabled=True, backend="memory", ttl=60, max_size=100),
        redis=RedisSettings(enabled=False),
        logging=LoggingSettings(level="ERROR", format="plain", output="stdout"),
    )
