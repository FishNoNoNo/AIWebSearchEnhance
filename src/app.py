from __future__ import annotations

from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat, client, health, search, stats
from src.cache.base import BaseCache
from src.cache.memory_cache import MemoryCache
from src.cache.redis_cache import RedisCache
from src.core.client_manager import ClientManager
from src.core.config_loader import AppConfig, get_config
from src.middleware.error_handler import setup_exception_handlers
from src.middleware.logging import RequestLoggingMiddleware
from src.models.analyzer import SearchAnalyzer
from src.models.organizer import SearchResultOrganizer
from src.pipeline.context_builder import ContextBuilder
from src.pipeline.executor import PipelineExecutor
from src.search.manager import SearchEngineManager
from src.utils.logger import configure_logging
from src.utils.metrics import MetricsCollector

VERSION = "1.0.0"


def create_app(config: AppConfig | None = None) -> FastAPI:
    config = config or get_config()
    configure_logging(config.logging)
    metrics = MetricsCollector()
    cache = _create_cache(config)
    client_manager = ClientManager()
    search_manager = SearchEngineManager.from_settings(
        config.search_engines,
        cache=cache if config.cache.enabled else None,
        cache_ttl=config.cache.ttl,
        metrics=metrics,
    )
    analyzer = SearchAnalyzer(config.analysis_model)
    organizer = SearchResultOrganizer()
    pipeline = PipelineExecutor(
        client_manager=client_manager,
        analyzer=analyzer,
        search_manager=search_manager,
        organizer=organizer,
        context_builder=ContextBuilder(),
        strategy=config.search_strategy,
        metrics=metrics,
    )

    app = FastAPI(title="AI Web Search", version=VERSION)
    app.state.version = VERSION
    app.state.started_at = monotonic()
    app.state.config = config
    app.state.metrics = metrics
    app.state.cache = cache
    app.state.client_manager = client_manager
    app.state.search_manager = search_manager
    app.state.pipeline = pipeline

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    setup_exception_handlers(app)
    app.include_router(client.router)
    app.include_router(chat.router)
    app.include_router(search.router)
    app.include_router(health.router)
    app.include_router(stats.router)
    return app


def _create_cache(config: AppConfig) -> BaseCache:
    if config.cache.backend == "redis" and config.redis.enabled:
        try:
            return RedisCache(config.redis)
        except Exception:
            pass
    return MemoryCache(
        ttl=config.cache.ttl,
        max_size=config.cache.max_size,
        enabled=config.cache.enabled,
    )


app = create_app()
