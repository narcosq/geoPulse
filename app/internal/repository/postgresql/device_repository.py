"""Device repository."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.internal.repository.repository import Repository
from app.pkg.db.models.device import Device, DeviceStatus
from app.pkg.models.schemas.geolocation import DeviceCreate, DeviceUpdate, DeviceResponse


__all__ = ["DeviceRepository"]


class DeviceRepository(Repository):
    """Repository for device operations."""

    async def create(self, device_data: DeviceCreate) -> Device:
        """Create a new device."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            device = Device(
                device_id=device_data.device_id,
                user_id=device_data.user_id,
                name=device_data.name,
                platform=device_data.platform,
                fcm_token=device_data.fcm_token,
                apns_token=device_data.apns_token,
                telegram_chat_id=device_data.telegram_chat_id,
                metadata=device_data.metadata,
            )
            session.add(device)
            await session.flush()
            await session.refresh(device)
            return device

    async def read_by_device_id(self, device_id: str) -> Optional[Device]:
        """Read device by device_id."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Device).where(Device.device_id == device_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def read_by_id(self, device_id: int) -> Optional[Device]:
        """Read device by ID."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Device).where(Device.id == device_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def read_by_user_id(self, user_id: str) -> List[Device]:
        """Read all devices for a user."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            stmt = select(Device).where(Device.user_id == user_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, device_id: str, device_data: DeviceUpdate) -> Optional[Device]:
        """Update device."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            device = await self.read_by_device_id(device_id)
            if not device:
                return None

            update_data = device_data.model_dump(exclude_unset=True)
            stmt = update(Device).where(Device.id == device.id).values(**update_data)
            await session.execute(stmt)
            await session.refresh(device)
            return device

    async def update_last_seen(self, device_id: str) -> None:
        """Update device last seen timestamp."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            from datetime import datetime, timezone
            stmt = update(Device).where(Device.device_id == device_id).values(
                last_seen=datetime.now(timezone.utc)
            )
            await session.execute(stmt)

    async def delete(self, device_id: str) -> bool:
        """Delete device."""
        async with self._sqlalchemy.session() as session:  # type: AsyncSession
            device = await self.read_by_device_id(device_id)
            if not device:
                return False
            await session.delete(device)
            return True

