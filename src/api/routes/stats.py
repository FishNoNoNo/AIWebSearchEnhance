from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["stats"])


@router.get("/v1/stats")
async def stats(request: Request) -> dict[str, object]:
    snapshot = request.app.state.metrics.snapshot()
    snapshot["active_clients"] = request.app.state.client_manager.count()
    return snapshot
