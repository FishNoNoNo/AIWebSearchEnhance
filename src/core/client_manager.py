from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from src.api.models.request import ClientInitRequest
from src.core.exceptions import ClientNotFoundError, InvalidRequestError
from src.models.base import BaseModelClient, ModelClientConfig
from src.models.factories import ModelFactory


@dataclass(slots=True)
class ManagedClient:
    client_id: str
    config: ModelClientConfig
    client: BaseModelClient
    created_at: datetime


class ClientManager:
    def __init__(self, factory: ModelFactory | None = None) -> None:
        self._factory = factory or ModelFactory()
        self._clients: dict[str, ManagedClient] = {}

    def create_client(self, request: ClientInitRequest) -> ManagedClient:
        if not request.api_key:
            raise InvalidRequestError("api_key is required")
        config = ModelClientConfig(
            provider=request.provider,
            api_key=request.api_key,
            base_url=str(request.base_url),
            model=request.model,
            organization=request.organization,
            timeout=request.timeout,
            default_headers=request.default_headers or {},
            api_version=request.api_version,
        )
        client_id = "cli_" + secrets.token_urlsafe(18).replace("-", "").replace("_", "")[:24]
        client = self._factory.create(config)
        managed = ManagedClient(
            client_id=client_id,
            config=config,
            client=client,
            created_at=datetime.now(timezone.utc),
        )
        self._clients[client_id] = managed
        return managed

    def get_client(self, client_id: str) -> ManagedClient:
        try:
            return self._clients[client_id]
        except KeyError as exc:
            raise ClientNotFoundError(f"Client not found: {client_id}") from exc

    def count(self) -> int:
        return len(self._clients)

    def clear(self) -> None:
        self._clients.clear()
