"""Kafka producer for event-driven architecture."""
import json
from typing import Dict, Any, Optional
from datetime import datetime
from aiokafka import AIOKafkaProducer
from app.pkg.logger import logger
from app.pkg.settings.settings import get_settings

__all__ = ["KafkaProducer"]


class KafkaProducer:
    """Kafka producer for sending events."""

    def __init__(self):
        self.settings = get_settings()
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        """Start Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.KAFKA.BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self):
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send_event(
        self,
        topic: str,
        event_type: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
    ):
        """Send event to Kafka topic.

        Args:
            topic: Kafka topic name
            event_type: Event type (e.g., "location.update", "geofence.enter")
            payload: Event payload
            key: Optional message key for partitioning
        """
        if not self.producer:
            logger.warning("Kafka producer not started. Cannot send event.")
            return

        try:
            full_topic = f"{self.settings.KAFKA.TOPICS_PREFIX}.{topic}"
            event = {
                "event_type": event_type,
                "timestamp": str(datetime.utcnow()),
                "payload": payload,
            }
            await self.producer.send(full_topic, value=event, key=key.encode() if key else None)
            logger.debug(f"Sent event {event_type} to topic {full_topic}")
        except Exception as e:
            logger.error(f"Failed to send event to Kafka: {e}")
            raise

    async def send_location_event(self, device_id: str, location_data: Dict[str, Any]):
        """Send location update event."""
        await self.send_event(
            topic="locations",
            event_type="location.update",
            payload={"device_id": device_id, **location_data},
            key=device_id,
        )

    async def send_geofence_event(
        self, device_id: str, geofence_id: int, event_type: str, location_data: Dict[str, Any]
    ):
        """Send geofence event (enter/exit)."""
        await self.send_event(
            topic="geofences",
            event_type=f"geofence.{event_type}",
            payload={
                "device_id": device_id,
                "geofence_id": geofence_id,
                **location_data,
            },
            key=device_id,
        )

