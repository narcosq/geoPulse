"""FastAPI dependencies для локализации."""

from typing import Annotated
from fastapi import Header, Depends, Request

from app.pkg.localization import Language
from app.internal.pkg.middlewares.localization import get_request_language


def get_language_from_header(
    accept_language: Annotated[str, Header(
        description="Язык интерфейса (ru, ky, en)",
        example="ru",
        alias="Accept-Language"
    )] = "ru"
) -> Language:
    """
    Получить язык из заголовка Accept-Language.

    Поддерживаемые языки:
    - ru: Русский (по умолчанию)
    - ky: Кыргызский
    - en: Английский

    Args:
        accept_language: Заголовок Accept-Language

    Returns:
        Language: Объект языка
    """
    # Парсим первый язык из заголовка
    language_code = accept_language.split(",")[0].split("-")[0].split(";")[0].lower()

    # Мапим на поддерживаемые языки
    language_mapping = {
        "ru": Language.RU,
        "ky": Language.KY,
        "kg": Language.KY,  # Альтернативный код для кыргызского
        "en": Language.EN,
    }

    return language_mapping.get(language_code, Language.RU)


def get_language_from_request(request: Request) -> Language:
    """
    Получить язык из состояния запроса (установленного middleware).

    Args:
        request: FastAPI request объект

    Returns:
        Language: Объект языка
    """
    return get_request_language(request)


# Type aliases для удобства
LanguageFromHeader = Annotated[Language, Depends(get_language_from_header)]
LanguageFromRequest = Annotated[Language, Depends(get_language_from_request)]