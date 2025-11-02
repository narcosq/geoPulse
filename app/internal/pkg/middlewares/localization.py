"""Localization middleware."""

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.pkg.localization import Language


class LocalizationMiddleware(BaseHTTPMiddleware):
    """Middleware for determining user language from headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and determine language."""
        # Get language from Accept-Language header
        accept_language = request.headers.get("Accept-Language", "ru")

        # Parse the first language from Accept-Language header
        # Format: "en-US,en;q=0.9,ru;q=0.8" -> "en"
        language_code = accept_language.split(",")[0].split("-")[0].split(";")[0].lower()

        # Map language codes to supported languages
        language_mapping = {
            "ru": Language.RU,
            "ky": Language.KY,
            "kg": Language.KY,  # Alternative code for Kyrgyz
            "en": Language.EN,
        }

        # Default to Russian if language not supported
        language = language_mapping.get(language_code, Language.RU)

        # Store language in request state
        request.state.language = language

        response = await call_next(request)
        return response


def get_request_language(request: Request) -> Language:
    """Get language from request state."""
    return getattr(request.state, "language", Language.RU)