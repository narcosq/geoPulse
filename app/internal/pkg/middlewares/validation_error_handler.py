import uuid
import logging
from enum import Enum
from typing import Any, Dict, List, Union

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.internal.pkg.middlewares.localization import get_request_language
from app.pkg.localization import get_translator, Language

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Коды ошибок и ключи валидации
# ──────────────────────────────────────────────

class ErrorCode(int, Enum):
    """Коды ошибок API."""
    VALIDATION_FAILED = 40001


class ValidationErrorKey(str, Enum):
    """Ключи переводов для ошибок валидации."""
    REQUIRED = "validation.required"
    STRING_REQUIRED = "validation.string_required"
    INTEGER_REQUIRED = "validation.integer_required"
    NUMBER_REQUIRED = "validation.number_required"
    INVALID_VALUE = "validation.invalid_value"
    INVALID_TYPE = "validation.invalid_type"
    GREATER_THAN = "validation.greater_than"
    GREATER_THAN_EQUAL = "validation.greater_than_equal"
    LESS_THAN = "validation.less_than"
    LESS_THAN_EQUAL = "validation.less_than_equal"
    INVALID_CHOICE = "validation.invalid_choice"
    INVALID_BANK_TYPE = "validation.invalid_bank_type"
    INVALID_CREDIT_TYPE = "validation.invalid_credit_type"
    INVALID_FORMAT = "validation.invalid_format"


ERROR_KEY_MAPPING: dict[str, ValidationErrorKey] = {
    "missing": ValidationErrorKey.REQUIRED,
    "string_type": ValidationErrorKey.STRING_REQUIRED,
    "int_parsing": ValidationErrorKey.INTEGER_REQUIRED,
    "float_parsing": ValidationErrorKey.NUMBER_REQUIRED,
    "value_error": ValidationErrorKey.INVALID_VALUE,
    "type_error": ValidationErrorKey.INVALID_TYPE,
    "greater_than": ValidationErrorKey.GREATER_THAN,
    "greater_than_equal": ValidationErrorKey.GREATER_THAN_EQUAL,
    "less_than": ValidationErrorKey.LESS_THAN,
    "less_than_equal": ValidationErrorKey.LESS_THAN_EQUAL,
    "literal_error": ValidationErrorKey.INVALID_CHOICE,
    "enum": ValidationErrorKey.INVALID_CHOICE,
}


# ──────────────────────────────────────────────
# Middleware для локализованных ошибок валидации
# ──────────────────────────────────────────────

class LocalizedValidationErrorHandler(BaseHTTPMiddleware):
    """Middleware для локализации ошибок валидации."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except (RequestValidationError, ValidationError) as exc:
            return self.handle_validation_error(request, exc)

    def handle_validation_error(
        self,
        request: Request,
        exc: Union[RequestValidationError, ValidationError],
    ) -> JSONResponse:
        trace_id = str(uuid.uuid4())
        language = get_request_language(request)
        translator = get_translator()

        details = self._build_error_details(exc.errors(), language, translator)

        logger.warning(f"[{trace_id}] Validation error at {request.url.path}: {details}")

        return JSONResponse(
            status_code=422,
            content={
                "outcome": "error",
                "code": ErrorCode.VALIDATION_FAILED,
                "trace_id": trace_id,
                "user_message": translator.t("errors.validation_failed", language),
                "developer_message": "Validation failed",
                "details": details,
            },
        )

    @staticmethod
    def _build_error_details(
        errors: List[Dict[str, Any]],
        language: Language,
        translator,
    ) -> List[Dict[str, Any]]:
        details: List[Dict[str, Any]] = []
        for error in errors:
            field_name = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            error_type = error["type"]
            ctx = error.get("ctx", {}) or {}

            if error_type == "enum":
                expected = ctx.get("expected", [])
                choices = (
                    ", ".join(map(str, expected))
                    if isinstance(expected, (list, tuple))
                    else str(expected)
                )
                if "bank_type" in field_name:
                    key = ValidationErrorKey.INVALID_BANK_TYPE
                elif "credit_type" in field_name:
                    key = ValidationErrorKey.INVALID_CREDIT_TYPE
                else:
                    key = ValidationErrorKey.INVALID_CHOICE
                localized_message = translator.t(key, language, choices=choices)
            else:
                key = ERROR_KEY_MAPPING.get(error_type, ValidationErrorKey.INVALID_FORMAT)
                params: Dict[str, Any] = {}
                if error_type in {"greater_than", "greater_than_equal"}:
                    params["min"] = ctx.get("gt") or ctx.get("ge")
                elif error_type in {"less_than", "less_than_equal"}:
                    params["max"] = ctx.get("lt") or ctx.get("le")
                localized_message = translator.t(key, language, **params)

            details.append(
                {"field": field_name, "message": localized_message, "type": error_type}
            )
        return details


# ──────────────────────────────────────────────
# Exception handlers
# ──────────────────────────────────────────────

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации для FastAPI (без middleware)."""
    handler = LocalizedValidationErrorHandler(None)  # type: ignore
    return handler.handle_validation_error(request, exc)


def create_validation_error_handlers():
    """Создать список обработчиков для app.add_exception_handler."""
    return [
        {"exception": RequestValidationError, "handler": validation_exception_handler}
    ]
