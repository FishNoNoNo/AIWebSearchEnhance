from __future__ import annotations

from time import monotonic

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = monotonic()
        try:
            response = await call_next(request)
        except Exception:
            request.app.state.metrics.record_error()
            raise
        elapsed_ms = round((monotonic() - started) * 1000, 2)
        request.app.state.metrics.record_request(elapsed_ms)
        logger.info(
            "request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=elapsed_ms,
        )
        return response
