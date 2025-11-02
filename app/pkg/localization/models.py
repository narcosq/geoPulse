"""Localization models."""

from enum import Enum


class Language(str, Enum):
    """Supported languages."""
    RU = "ru"
    KY = "ky"
    EN = "en"