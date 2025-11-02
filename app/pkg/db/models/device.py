"""Device model for tracking mobile devices."""
from sqlalchemy import (
    BigInteger, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.pkg.db.base import Base


class DevicePlatform(str, enum.Enum):
    """Device platform enum."""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


class DeviceStatus(str, enum.Enum):
    """Device status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Device(Base):
    """Device model."""
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    platform: Mapped[DevicePlatform] = mapped_column(SQLEnum(DevicePlatform), nullable=False)
    status: Mapped[DeviceStatus] = mapped_column(SQLEnum(DeviceStatus), default=DeviceStatus.ACTIVE, nullable=False)
    
    # Push notification tokens
    fcm_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    apns_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # Telegram integration
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_seen: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    locations: Mapped[list["Location"]] = relationship("Location", back_populates="device", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="device", cascade="all, delete-orphan")

