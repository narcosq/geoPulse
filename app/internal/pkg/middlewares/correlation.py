import uuid
import contextvars
from typing import Callable, Awaitable

from fastapi import Header, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

X_REQUEST_ID = "X-Request-Id"
X_IDEMPOTENCY_KEY = "X-Idempotency-Key"

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
idempotency_key_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("idempotency_key", default="-")


def common_headers(
    x_request_id: str | None = Header(None, alias=X_REQUEST_ID, description="Correlation ID запроса"),
    x_idempotency_key: str | None = Header(
        None, alias=X_IDEMPOTENCY_KEY, description="Idempotency Key (обязателен для POST/PUT)"
    ),
    accept_language: str | None = Header(
        None, alias="Accept-Language", description="Accept language",
        examples=["en-US", "en"], example="en-US",
    ),
):
    return {X_REQUEST_ID: x_request_id, X_IDEMPOTENCY_KEY: x_idempotency_key, accept_language: accept_language}


class CorrelationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        req_id = request.headers.get(X_REQUEST_ID) or str(uuid.uuid4())
        request_id_ctx.set(req_id)

        # idem_key = request.headers.get(X_IDEMPOTENCY_KEY)
        # idempotency_key_ctx.set(idem_key or "-")

        response = await call_next(request)
        response.headers.setdefault(X_REQUEST_ID, req_id)
        return response
