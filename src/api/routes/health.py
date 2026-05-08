from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    app_state = request.app.state
    search_checks = await app_state.search_manager.health_check()
    redis_status = "healthy" if await app_state.cache.health_check() else "degraded"
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app_state.version,
        "checks": {
            "config": "healthy",
            "analysis_model": "healthy"
            if app_state.config.analysis_model.api_key
            else "fallback_heuristic",
            "redis": redis_status,
            "search_engines": {
                name: "healthy" if data["available"] else "degraded"
                for name, data in search_checks.items()
            },
        },
        "uptime_seconds": round(monotonic() - app_state.started_at, 2),
    }


@router.get("/ready")
async def ready() -> dict[str, bool]:
    return {"ready": True}
