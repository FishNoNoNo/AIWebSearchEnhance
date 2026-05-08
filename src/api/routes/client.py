from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models.request import ClientInitRequest
from src.api.models.response import ClientInitResponse

router = APIRouter(prefix="/v1/client", tags=["client"])


@router.post("/init", response_model=ClientInitResponse)
async def init_client(payload: ClientInitRequest, request: Request) -> ClientInitResponse:
    managed = request.app.state.client_manager.create_client(payload)
    return ClientInitResponse(client_id=managed.client_id)
