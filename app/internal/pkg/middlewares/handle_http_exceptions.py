"""
Handlers for API and internal exceptions.

Catches:
- BaseAPIException (your custom business errors)
- Any unhandled Exception

Always returns JSON with unified format.
"""

import logging
import uuid
from fastapi import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.internal.pkg.middlewares.correlation import request_id_ctx, idempotency_key_ctx
from app.pkg.models.base import BaseAPIException
from app.pkg.models.exceptions.api import InternalServerError

logger = logging.getLogger(__name__)

__all__ = ["handle_api_exceptions", "handle_internal_exception"]


async def handle_api_exceptions(request: Request, exc: BaseAPIException):
    """Обработка всех кастомных ошибок (унаследованных от BaseAPIException)."""
    trace_id = str(uuid.uuid4())
    request_id = request_id_ctx.get()
    idempotency_key = idempotency_key_ctx.get()

    error_payload = {
        **exc.error.model_dump(),
        "trace_id": trace_id,
        "request_id": request_id,
        "idempotency_key": idempotency_key,
        "developer_message": exc.error.developer_message or "API exception",
    }

    logger.warning(
        f"[{trace_id}] API Exception at {request.method} {request.url.path}: {error_payload}"
    )

    return JSONResponse(
        status_code=exc.status_code or status.HTTP_400_BAD_REQUEST,
        content=error_payload,
    )


async def handle_internal_exception(request: Request, exc: Exception):
    """Обработка всех непойманных ошибок (runtime, system, etc.)."""
    trace_id = str(uuid.uuid4())
    error = InternalServerError(trace_id=trace_id)
    request_id = request_id_ctx.get()
    idempotency_key = idempotency_key_ctx.get()


    payload = {
        **error.error.model_dump(),
        "trace_id": trace_id,
        "request_id": request_id,
        "idempotency_key": idempotency_key,
        "developer_message": f"Unhandled {type(exc).__name__}",
    }

    logger.exception(
        f"[{trace_id}] Unhandled exception at {request.method} {request.url.path}: {repr(exc)}",
        extra={"trace_id": trace_id, "path": str(request.url.path), "method": request.method},
    )

    return JSONResponse(status_code=error.status_code, content=payload)
