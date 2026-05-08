from __future__ import annotations

from typing import Any


class AppException(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidRequestError(AppException):
    status_code = 400
    code = "INVALID_REQUEST"


class AuthError(AppException):
    status_code = 401
    code = "AUTH_ERROR"


class ClientNotFoundError(AppException):
    status_code = 404
    code = "CLIENT_NOT_FOUND"


class TimeoutError(AppException):
    status_code = 408
    code = "TIMEOUT"


class RateLimitError(AppException):
    status_code = 429
    code = "RATE_LIMIT"


class SearchEngineError(AppException):
    status_code = 502
    code = "SEARCH_ENGINE_ERROR"


class ModelUnavailableError(AppException):
    status_code = 503
    code = "MODEL_UNAVAILABLE"
