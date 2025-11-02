from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel
from fastapi import status
from fastapi.exceptions import HTTPException

from app.pkg.localization import get_translator, Language

__all__ = ["BaseAPIException", "LocalizedAPIException"]


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    outcome: Literal["error", "success"] = "error"
    code: int
    user_message: str
    developer_message: str
    details: Optional[List[ErrorDetail]] = None
    trace_id: Optional[str] = None  # для корреляции логов/запросов


class BaseAPIException(HTTPException):
    """Базовое исключение для API (с единым контрактом и логированием)."""
    default_user_message: str = "Внутренняя ошибка сервера"
    default_developer_message: str = "Internal server error"
    default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code: int = 10001

    error: ErrorResponse

    def __init__(
        self,
        *,
        user_message: Optional[str] = None,
        developer_message: Optional[str] = None,
        status_code: Optional[int] = None,
        code: Optional[int] = None,
        details: Optional[List[ErrorDetail | Dict]] = None,
        trace_id: Optional[str] = None,
    ):
        self.error = ErrorResponse(
            code=code or self.default_code,
            user_message=user_message or self.default_user_message,
            developer_message=developer_message or self.default_developer_message,
            details=details,
            trace_id=trace_id,
        )
        super().__init__(
            status_code=status_code or self.default_status_code,
            detail=self.error.model_dump()
        )


class LocalizedAPIException(BaseAPIException):
    """Локализованное исключение API с поддержкой переводов."""

    # Ключи для переводов (переопределяются в наследниках)
    user_message_key: Optional[str] = None
    developer_message_key: Optional[str] = None

    def __init__(
        self,
        *,
        language: Language = Language.RU,
        user_message: Optional[str] = None,
        developer_message: Optional[str] = None,
        status_code: Optional[int] = None,
        code: Optional[int] = None,
        details: Optional[List[ErrorDetail | Dict]] = None,
        trace_id: Optional[str] = None,
        translation_params: Optional[Dict[str, Any]] = None,
    ):
        translator = get_translator()

        # Переводим сообщения, если заданы ключи
        if user_message is None and self.user_message_key:
            user_message = translator.t(
                self.user_message_key,
                language,
                **(translation_params or {})
            )

        if developer_message is None and self.developer_message_key:
            developer_message = translator.t(
                self.developer_message_key,
                language,
                **(translation_params or {})
            )

        super().__init__(
            user_message=user_message,
            developer_message=developer_message,
            status_code=status_code,
            code=code,
            details=details,
            trace_id=trace_id,
        )
