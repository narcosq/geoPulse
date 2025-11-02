"""Локализованный обработчик ошибок."""

from typing import Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.pkg.models.base.exception import LocalizedAPIException, BaseAPIException
from app.internal.pkg.middlewares.localization import get_request_language
from app.pkg.localization import get_translator, Language


class LocalizedErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware для локализации ошибок."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Обработать запрос и локализовать ошибки."""
        try:
            response = await call_next(request)
            return response
        except LocalizedAPIException as exc:
            # Исключение уже локализовано
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        except BaseAPIException as exc:
            # Попытаться локализовать базовое исключение
            language = get_request_language(request)
            return await self._localize_base_exception(exc, language)
        except Exception as exc:
            # Неожиданное исключение - залогировать и вернуть общую ошибку
            language = get_request_language(request)
            return await self._handle_unexpected_exception(exc, language, request)

    async def _localize_base_exception(
        self,
        exc: BaseAPIException,
        language: Language
    ) -> JSONResponse:
        """Локализовать базовое исключение."""
        translator = get_translator()

        # Попытаться найти переводы для общих ошибок
        error_detail = exc.detail.copy()

        # Переводы для стандартных HTTP ошибок
        if exc.status_code == 404:
            error_detail["user_message"] = translator.t("errors.not_found", language)
        elif exc.status_code == 401:
            error_detail["user_message"] = translator.t("errors.unauthorized", language)
        elif exc.status_code == 403:
            error_detail["user_message"] = translator.t("errors.forbidden", language)
        elif exc.status_code == 422:
            error_detail["user_message"] = translator.t("errors.validation_failed", language)
        elif exc.status_code >= 500:
            error_detail["user_message"] = translator.t("errors.internal_error", language)

        return JSONResponse(
            status_code=exc.status_code,
            content=error_detail
        )

    async def _handle_unexpected_exception(
        self,
        exc: Exception,
        language: Language,
        request: Request
    ) -> JSONResponse:
        """Обработать неожиданное исключение."""
        from app.pkg.logger import logger

        translator = get_translator()

        # Залогировать ошибку
        logger.error(
            "Unexpected exception occurred",
            extra={
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "request_path": request.url.path,
                "request_method": request.method,
            }
        )

        return JSONResponse(
            status_code=500,
            content={
                "outcome": "error",
                "code": 10001,
                "user_message": translator.t("errors.internal_error", language),
                "developer_message": "Internal server error",
            }
        )


def create_localized_credit_exception(
    exception_class: type,
    language: Language,
    **translation_params
) -> LocalizedAPIException:
    """
    Создать локализованное кредитное исключение.

    Args:
        exception_class: Класс исключения
        language: Язык для локализации
        **translation_params: Параметры для шаблонов переводов

    Returns:
        Локализованное исключение
    """
    return exception_class(
        language=language,
        translation_params=translation_params
    )


# Utility функции для частых случаев
def raise_invalid_amount_error(language: Language, min_amount: float, max_amount: float):
    """Поднять ошибку неверной суммы с параметрами."""
    from app.pkg.models.exceptions.credit import InvalidProductException

    raise create_localized_credit_exception(
        InvalidProductException,
        language,
        min_amount=min_amount,
        max_amount=max_amount
    )


def raise_invalid_term_error(language: Language, min_term: int, max_term: int):
    """Поднять ошибку неверного срока с параметрами."""
    from app.pkg.models.exceptions.credit import InvalidMaxTermException

    raise create_localized_credit_exception(
        InvalidMaxTermException,
        language,
        min_term=min_term,
        max_term=max_term
    )