"""Celery tasks for notification processing."""
from typing import Optional, Dict, Any
from tasks.celery_app import celery_app
from app.pkg.logger import logger

__all__ = ["send_notification_task"]


@celery_app.task(name="notifications.send")
def send_notification_task(
    notification_id: int,
    device_id: str,
    notification_type: str,
    title: str,
    message: str,
    fcm_token: Optional[str] = None,
    telegram_chat_id: Optional[str] = None,
    enable_sound: bool = True,
    location_data: Optional[Dict[str, Any]] = None,
):
    """Send notification task.

    Args:
        notification_id: Notification ID
        device_id: Device ID
        notification_type: Type of notification (push/telegram)
        title: Notification title
        message: Notification message
        fcm_token: FCM token for push notifications
        telegram_chat_id: Telegram chat ID
        enable_sound: Enable sound
        location_data: Optional location data
    """
    try:
        # Import here to avoid circular dependencies
        from app.pkg.clients.firebase import FirebaseClient
        from app.pkg.clients.telegram import TelegramClient
        from app.internal.repository.postgresql.notification_repository import (
            NotificationRepository,
            NotificationLogRepository,
        )
        from app.pkg.connectors import Connectors
        from app.pkg.db.models.notification import NotificationStatus
        import asyncio

        async def _send():
            firebase_client = FirebaseClient()
            telegram_client = TelegramClient()
            connectors = Connectors()
            notification_repo = NotificationRepository(sqlalchemy=connectors.sqlalchemy())
            log_repo = NotificationLogRepository(sqlalchemy=connectors.sqlalchemy())

            message_id = None
            error_message = None

            try:
                if notification_type == "push" and fcm_token:
                    message_id = await firebase_client.send_push_notification(
                        token=fcm_token,
                        title=title,
                        body=message,
                        sound=enable_sound,
                        data=location_data or {},
                    )
                    if message_id:
                        await notification_repo.update_status(
                            notification_id,
                            NotificationStatus.SENT,
                            fcm_message_id=message_id,
                        )
                        await log_repo.create(notification_id, "sent", {"message_id": message_id})
                    else:
                        await notification_repo.update_status(
                            notification_id, NotificationStatus.FAILED, error_message="FCM send failed"
                        )

                elif notification_type == "telegram" and telegram_chat_id:
                    text = f"*{title}*\n\n{message}"
                    if location_data:
                        text += f"\n\n📍 Location: {location_data.get('latitude')}, {location_data.get('longitude')}"

                    message_id = await telegram_client.send_message(
                        chat_id=telegram_chat_id,
                        text=text,
                        disable_notification=not enable_sound,
                    )
                    if message_id:
                        await notification_repo.update_status(
                            notification_id,
                            NotificationStatus.SENT,
                            telegram_message_id=message_id,
                        )
                        await log_repo.create(notification_id, "sent", {"message_id": message_id})
                    else:
                        await notification_repo.update_status(
                            notification_id,
                            NotificationStatus.FAILED,
                            error_message="Telegram send failed",
                        )

            except Exception as e:
                error_message = str(e)
                logger.error(f"Failed to send notification {notification_id}: {e}")
                await notification_repo.update_status(
                    notification_id, NotificationStatus.FAILED, error_message=error_message
                )
                await log_repo.create(notification_id, "failed", error_message=error_message)

        # Run async function in event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_send())

    except Exception as e:
        logger.error(f"Notification task failed: {e}")


@celery_app.task(name="notifications.process_pending")
def process_pending_notifications_task():
    """Process pending notifications."""
    try:
        import asyncio
        from app.internal.repository.postgresql.notification_repository import (
            NotificationRepository,
        )
        from app.pkg.connectors import Connectors
        from app.pkg.db.models.notification import NotificationStatus

        async def _process():
            connectors = Connectors()
            notification_repo = NotificationRepository(sqlalchemy=connectors.sqlalchemy())
            notifications = await notification_repo.get_pending_notifications(limit=100)

            for notification in notifications:
                from app.pkg.db.models.device import Device
                from app.internal.repository.postgresql.device_repository import DeviceRepository

                device_repo = DeviceRepository(sqlalchemy=connectors.sqlalchemy())
                device = await device_repo.read_by_id(notification.device_id)

                if device:
                    send_notification_task.delay(
                        notification_id=notification.id,
                        device_id=device.device_id,
                        notification_type=notification.notification_type.value,
                        title=notification.title,
                        message=notification.message,
                        fcm_token=device.fcm_token,
                        telegram_chat_id=device.telegram_chat_id,
                        enable_sound=notification.enable_sound,
                        location_data=notification.location_data,
                    )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(_process())

    except Exception as e:
        logger.error(f"Failed to process pending notifications: {e}")

