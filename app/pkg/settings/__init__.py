"""Global point to cached settings."""

from .settings import Settings, get_settings

__all__ = ["settings", "Settings"]

settings: Settings = get_settings()
