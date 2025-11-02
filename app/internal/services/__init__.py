from dependency_injector import containers, providers

from app.internal import entity
from app.internal.repository import Repositories, postgresql
from app.internal.services.healthz import HealthzService
from app.internal.services.geolocation_service import GeolocationService

from app.pkg.connectors import Connectors
from app.pkg.clients import Clients

__all__ = ["Services"]


class Services(containers.DeclarativeContainer):
    """Containers with services."""

    repositories: postgresql.Repositories = providers.Container(
        Repositories.postgres,  # type: ignore
    )
    entities: entity.Entities = providers.Container(
        entity.Entities,  # type: ignore
    )
    connectors = providers.Container(
        Connectors,  # type: ignore
    )
    clients = providers.Container(
        Clients,  # type: ignore
    )

    healthz: HealthzService = providers.Factory(
        HealthzService,
        healthz_repository=repositories.healthz_repository,
        redis_connector=connectors.redis,
    )

    geolocation: GeolocationService = providers.Factory(
        GeolocationService,
        device_repository=repositories.device_repository,
        location_repository=repositories.location_repository,
        geofence_repository=repositories.geofence_repository,
        device_geofence_repository=repositories.device_geofence_repository,
        notification_repository=repositories.notification_repository,
        google_maps_client=clients.google_maps_client,
        kafka_producer=providers.Singleton(lambda: None),  # TODO: Initialize Kafka producer properly
    )
