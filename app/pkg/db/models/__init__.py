# Re-export ORM models so they are importable for Alembic autogenerate
from .device import Device, DevicePlatform, DeviceStatus
from .location import Location
from .geofence import Geofence, GeofenceType, GeofenceStatus, DeviceGeofence
from .notification import (
    Notification,
    NotificationType,
    NotificationStatus,
    NotificationPriority,
    NotificationLog,
)

__all__ = [
    "Device",
    "DevicePlatform",
    "DeviceStatus",
    "Location",
    "Geofence",
    "GeofenceType",
    "GeofenceStatus",
    "DeviceGeofence",
    "Notification",
    "NotificationType",
    "NotificationStatus",
    "NotificationPriority",
    "NotificationLog",
]
