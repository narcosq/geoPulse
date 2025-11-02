from dependency_injector import containers, providers

from .firebase import FirebaseClient
from .telegram import TelegramClient
from .google_maps import GoogleMapsClient

__all__ = ["Clients", "FirebaseClient", "TelegramClient", "GoogleMapsClient"]


class Clients(containers.DeclarativeContainer):
    """Declarative container with clients."""

    firebase_client = providers.Singleton(FirebaseClient)
    telegram_client = providers.Singleton(TelegramClient)
    google_maps_client = providers.Singleton(GoogleMapsClient)
