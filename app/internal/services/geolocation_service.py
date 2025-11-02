"""Geolocation service for processing device locations and geofences."""
from typing import List, Optional
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt
from shapely.geometry import Point, Polygon, Circle
from shapely.prepared import prep

from app.internal.repository.postgresql import (
    DeviceRepository,
    LocationRepository,
    GeofenceRepository,
    DeviceGeofenceRepository,
    NotificationRepository,
)
from app.pkg.clients.google_maps import GoogleMapsClient
from app.pkg.clients.kafka_producer import KafkaProducer
from app.pkg.db.models.geofence import GeofenceType
from app.pkg.db.models.notification import NotificationType, NotificationStatus, NotificationPriority
from app.pkg.models.schemas.geolocation import LocationCreate, NotificationCreate
from datetime import datetime, timezone
from app.pkg.logger import logger

__all__ = ["GeolocationService"]


def haversine_distance(lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal) -> float:
    """Calculate distance between two points using Haversine formula.

    Returns distance in meters.
    """
    R = 6371000  # Earth radius in meters
    lat1_rad = radians(float(lat1))
    lat2_rad = radians(float(lat2))
    delta_lat = radians(float(lat2 - lat1))
    delta_lon = radians(float(lon2 - lon1))

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c


def point_in_polygon(lat: Decimal, lon: Decimal, polygon_coords: List[List[Decimal]]) -> bool:
    """Check if point is inside polygon."""
    point = Point(float(lon), float(lat))
    polygon = Polygon([(float(lon), float(lat)) for lat, lon in polygon_coords])
    return polygon.contains(point)


def point_in_circle(
    lat: Decimal, lon: Decimal, center_lat: Decimal, center_lon: Decimal, radius_meters: Decimal
) -> bool:
    """Check if point is inside circle."""
    distance = haversine_distance(lat, lon, center_lat, center_lon)
    return distance <= float(radius_meters)


def point_in_rectangle(
    lat: Decimal,
    lon: Decimal,
    min_lat: Decimal,
    max_lat: Decimal,
    min_lon: Decimal,
    max_lon: Decimal,
) -> bool:
    """Check if point is inside rectangle."""
    return (
        min_lat <= lat <= max_lat
        and min_lon <= lon <= max_lon
    )


class GeolocationService:
    """Service for geolocation operations."""

    def __init__(
        self,
        device_repository: DeviceRepository,
        location_repository: LocationRepository,
        geofence_repository: GeofenceRepository,
        device_geofence_repository: DeviceGeofenceRepository,
        notification_repository: NotificationRepository,
        google_maps_client: GoogleMapsClient,
        kafka_producer: KafkaProducer,
    ):
        self.device_repository = device_repository
        self.location_repository = location_repository
        self.geofence_repository = geofence_repository
        self.device_geofence_repository = device_geofence_repository
        self.notification_repository = notification_repository
        self.google_maps_client = google_maps_client
        self.kafka_producer = kafka_producer

    async def process_location(self, device_id: str, location_data: LocationCreate):
        """Process device location update.

        This method:
        1. Saves location to database
        2. Updates device last_seen
        3. Checks geofences
        4. Triggers notifications if needed
        5. Publishes events to Kafka
        """
        # Get or create device
        device = await self.device_repository.read_by_device_id(device_id)
        if not device:
            logger.warning(f"Device {device_id} not found. Cannot process location.")
            return

        # Update device last_seen
        await self.device_repository.update_last_seen(device_id)

        # Save location
        location = await self.location_repository.create(device.id, location_data)

        # Reverse geocode if Google Maps is available
        if self.google_maps_client.client:
            try:
                address_info = await self.google_maps_client.reverse_geocode(
                    location_data.latitude, location_data.longitude
                )
                if address_info:
                    await self.location_repository.update_address(
                        location.id,
                        address_info.get("formatted_address", ""),
                        address_info.get("components", {}).get("city"),
                        address_info.get("components", {}).get("country"),
                    )
            except Exception as e:
                logger.error(f"Failed to reverse geocode: {e}")

        # Publish location event to Kafka
        try:
            await self.kafka_producer.send_location_event(
                device_id,
                {
                    "latitude": float(location_data.latitude),
                    "longitude": float(location_data.longitude),
                    "timestamp": location_data.timestamp.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish location event: {e}")

        # Check geofences
        await self.check_geofences(device.id, location_data.latitude, location_data.longitude)

    async def check_geofences(self, device_db_id: int, latitude: Decimal, longitude: Decimal):
        """Check if device is inside/outside geofences."""
        # Get device geofences
        device_geofences = await self.device_geofence_repository.get_by_device_id(device_db_id)
        device = await self.device_repository.read_by_id(device_db_id)

        for device_geofence in device_geofences:
            geofence = await self.geofence_repository.read_by_id(device_geofence.geofence_id)
            if not geofence or geofence.status.value != "active":
                continue

            # Check if point is inside geofence
            is_inside = False
            if geofence.geofence_type == GeofenceType.CIRCLE:
                is_inside = point_in_circle(
                    latitude,
                    longitude,
                    geofence.center_latitude,
                    geofence.center_longitude,
                    geofence.radius_meters,
                )
            elif geofence.geofence_type == GeofenceType.POLYGON:
                if geofence.polygon_coordinates:
                    is_inside = point_in_polygon(latitude, longitude, geofence.polygon_coordinates)
            elif geofence.geofence_type == GeofenceType.RECTANGLE:
                is_inside = point_in_rectangle(
                    latitude,
                    longitude,
                    geofence.min_latitude,
                    geofence.max_latitude,
                    geofence.min_longitude,
                    geofence.max_longitude,
                )

            # Handle state changes
            previous_state = device_geofence.is_inside
            if is_inside != previous_state:
                if is_inside:
                    # Device entered geofence
                    await self.device_geofence_repository.update_state(
                        device_db_id,
                        geofence.id,
                        is_inside=True,
                        entered_at=datetime.now(timezone.utc),
                    )

                    # Send enter notification
                    if geofence.notify_on_enter:
                        await self.send_geofence_notification(
                            device_db_id,
                            geofence,
                            "geofence_enter",
                            latitude,
                            longitude,
                        )

                    # Publish Kafka event
                    try:
                        await self.kafka_producer.send_geofence_event(
                            device.device_id,
                            geofence.id,
                            "enter",
                            {
                                "latitude": float(latitude),
                                "longitude": float(longitude),
                            },
                        )
                    except Exception as e:
                        logger.error(f"Failed to publish geofence enter event: {e}")

                else:
                    # Device exited geofence
                    await self.device_geofence_repository.update_state(
                        device_db_id,
                        geofence.id,
                        is_inside=False,
                        exited_at=datetime.now(timezone.utc),
                    )

                    # Send exit notification
                    if geofence.notify_on_exit:
                        await self.send_geofence_notification(
                            device_db_id,
                            geofence,
                            "geofence_exit",
                            latitude,
                            longitude,
                        )

                    # Publish Kafka event
                    try:
                        await self.kafka_producer.send_geofence_event(
                            device.device_id,
                            geofence.id,
                            "exit",
                            {
                                "latitude": float(latitude),
                                "longitude": float(longitude),
                            },
                        )
                    except Exception as e:
                        logger.error(f"Failed to publish geofence exit event: {e}")

    async def send_geofence_notification(
        self,
        device_db_id: int,
        geofence,
        event_type: str,
        latitude: Decimal,
        longitude: Decimal,
    ):
        """Send geofence notification."""
        device = await self.device_repository.read_by_id(device_db_id)
        if not device:
            return

        title = f"Geofence: {geofence.name}"
        message = geofence.notification_message or (
            f"Device {'entered' if event_type == 'geofence_enter' else 'exited'} geofence {geofence.name}"
        )

        # Create notification records
        if geofence.enable_push and device.fcm_token:
            notification_data = NotificationCreate(
                device_id=device.device_id,
                notification_type=NotificationType.PUSH,
                title=title,
                message=message,
                priority=NotificationPriority.HIGH,
                enable_sound=geofence.enable_sound,
                geofence_id=geofence.id,
                event_type=event_type,
                location_data={
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
            )
            notification = await self.notification_repository.create(device_db_id, notification_data)

            # Queue Celery task
            from tasks.notification_tasks import send_notification_task

            send_notification_task.delay(
                notification_id=notification.id,
                device_id=device.device_id,
                notification_type="push",
                title=title,
                message=message,
                fcm_token=device.fcm_token,
                enable_sound=geofence.enable_sound,
                location_data={
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
            )

        if geofence.enable_telegram and device.telegram_chat_id:
            notification_data = NotificationCreate(
                device_id=device.device_id,
                notification_type=NotificationType.TELEGRAM,
                title=title,
                message=message,
                priority=NotificationPriority.HIGH,
                enable_sound=geofence.enable_sound,
                geofence_id=geofence.id,
                event_type=event_type,
                location_data={
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
            )
            notification = await self.notification_repository.create(device_db_id, notification_data)

            # Queue Celery task
            from tasks.notification_tasks import send_notification_task

            send_notification_task.delay(
                notification_id=notification.id,
                device_id=device.device_id,
                notification_type="telegram",
                title=title,
                message=message,
                telegram_chat_id=device.telegram_chat_id,
                enable_sound=geofence.enable_sound,
                location_data={
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
            )

