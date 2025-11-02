"""Notification repository."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.internal.repository.repository import Repository
from app.pkg.db.models.notification import Notification, NotificationLog, NotificationStatus
from app.pkg.models.schemas.geolocation import NotificationCreate


__all__ = ["NotificationRepository", "NotificationLogRepository"]


class NotificationRepository(Repository):
    """Repository for notification operations."""

    async def create(self, device_db_id: int, notification_data: NotificationCreate) -> Notification:
        """Create a new notification."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            notification = Notification(
                device_id=device_db_id,
                geofence_id=notification_data.geofence_id,
                notification_type=notification_data.notification_type,
                title=notification_data.title,
                message=notification_data.message,
                priority=notification_data.priority,
                enable_sound=notification_data.enable_sound,
                event_type=notification_data.event_type,
                location_data=notification_data.location_data,
                scheduled_at=notification_data.scheduled_at,
            )
            session.add(notification)
            await session.flush()
            await session.refresh(notification)
            return notification

    async def read_by_id(self, notification_id: int) -> Optional[Notification]:
        """Read notification by ID."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def read_by_device_id(
        self,
        device_db_id: int,
        limit: int = 100,
        offset: int = 0,
        status: Optional[NotificationStatus] = None,
    ) -> List[Notification]:
        """Read notifications for a device."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Notification).where(Notification.device_id == device_db_id)
            if status:
                stmt = stmt.where(Notification.status == status)
            stmt = stmt.order_by(desc(Notification.created_at)).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_status(
        self,
        notification_id: int,
        status: NotificationStatus,
        fcm_message_id: Optional[str] = None,
        telegram_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Notification]:
        """Update notification status."""
        from datetime import datetime, timezone
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            update_data = {"status": status}
            if status == NotificationStatus.SENT:
                update_data["sent_at"] = datetime.now(timezone.utc)
                if fcm_message_id:
                    update_data["fcm_message_id"] = fcm_message_id
                if telegram_message_id:
                    update_data["telegram_message_id"] = telegram_message_id
            elif status == NotificationStatus.DELIVERED:
                update_data["delivered_at"] = datetime.now(timezone.utc)
            if error_message:
                update_data["error_message"] = error_message
                update_data["retry_count"] = Notification.retry_count + 1

            stmt = update(Notification).where(Notification.id == notification_id).values(**update_data)
            await session.execute(stmt)
            return await self.read_by_id(notification_id)

    async def get_pending_notifications(self, limit: int = 100) -> List[Notification]:
        """Get pending notifications."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            from datetime import datetime, timezone
            stmt = (
                select(Notification)
                .where(Notification.status == NotificationStatus.PENDING)
                .where(
                    (Notification.scheduled_at.is_(None))
                    | (Notification.scheduled_at <= datetime.now(timezone.utc))
                )
                .order_by(Notification.priority.desc(), Notification.created_at)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())


class NotificationLogRepository(Repository):
    """Repository for notification log operations."""

    async def create(
        self,
        notification_id: int,
        action: str,
        details: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> NotificationLog:
        """Create a new notification log entry."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            log = NotificationLog(
                notification_id=notification_id,
                action=action,
                details=details,
                error_message=error_message,
            )
            session.add(log)
            await session.flush()
            await session.refresh(log)
            return log

    async def read_by_notification_id(self, notification_id: int) -> List[NotificationLog]:
        """Read logs for a notification."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = (
                select(NotificationLog)
                .where(NotificationLog.notification_id == notification_id)
                .order_by(desc(NotificationLog.created_at))
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

