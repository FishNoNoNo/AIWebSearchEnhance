from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models.request import ClearCacheRequest, SearchRequest
from src.api.models.response import ClearCacheResponse, SearchOnlyResponse

router = APIRouter(tags=["search"])


@router.post("/v1/search", response_model=SearchOnlyResponse)
async def search(payload: SearchRequest, request: Request) -> SearchOnlyResponse:
    response = await request.app.state.search_manager.search(
        payload.query,
        max_results=payload.max_results,
        engine=payload.engine,
    )
    return SearchOnlyResponse(**response.model_dump())


@router.get("/v1/search/engines")
async def search_engines(request: Request) -> dict[str, object]:
    checks = await request.app.state.search_manager.health_check()
    engines = [
        {
            "name": name,
            "enabled": item["enabled"],
            "available": item["available"],
            "priority": item["priority"],
            "latency_ms": item["latency_ms"],
        }
        for name, item in sorted(checks.items(), key=lambda pair: pair[1]["priority"])
    ]
    default_engine = next((item["name"] for item in engines if item["available"]), None)
    return {"engines": engines, "default_engine": default_engine}


@router.post("/v1/cache/clear", response_model=ClearCacheResponse)
async def clear_cache(payload: ClearCacheRequest, request: Request) -> ClearCacheResponse:
    count = await request.app.state.cache.delete_pattern(payload.pattern)
    return ClearCacheResponse(cleared_count=count)
