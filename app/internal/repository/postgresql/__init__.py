from dependency_injector import containers, providers

from .healthz_orm import HealthzOrmRepository
from .device_repository import DeviceRepository
from .location_repository import LocationRepository
from .geofence_repository import GeofenceRepository, DeviceGeofenceRepository
from .notification_repository import NotificationRepository, NotificationLogRepository
from app.pkg.connectors import Connectors

__all__ = [
    "Repositories",
    "HealthzOrmRepository",
    "DeviceRepository",
    "LocationRepository",
    "GeofenceRepository",
    "DeviceGeofenceRepository",
    "NotificationRepository",
    "NotificationLogRepository",
]


class Repositories(containers.DeclarativeContainer):
    connectors = providers.Container(
        Connectors
    )

    healthz_repository = providers.Factory(
        HealthzOrmRepository,
        sqlalchemy=connectors.sqlalchemy,
    )

    device_repository = providers.Factory(
        DeviceRepository,
        sqlalchemy=connectors.sqlalchemy,
    )

    location_repository = providers.Factory(
        LocationRepository,
        sqlalchemy=connectors.sqlalchemy,
    )

    geofence_repository = providers.Factory(
        GeofenceRepository,
        sqlalchemy=connectors.sqlalchemy,
    )

    device_geofence_repository = providers.Factory(
        DeviceGeofenceRepository,
        sqlalchemy=connectors.sqlalchemy,
    )

    notification_repository = providers.Factory(
        NotificationRepository,
        sqlalchemy=connectors.sqlalchemy,
    )

    notification_log_repository = providers.Factory(
        NotificationLogRepository,
        sqlalchemy=connectors.sqlalchemy,
    )
