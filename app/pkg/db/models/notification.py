"""Notification models for tracking sent notifications."""
from sqlalchemy import (
    BigInteger, String, Text, DateTime, Boolean, Enum as SQLEnum, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.pkg.db.base import Base


class NotificationType(str, enum.Enum):
    """Notification type enum."""
    PUSH = "push"
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"


class NotificationStatus(str, enum.Enum):
    """Notification status enum."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class NotificationPriority(str, enum.Enum):
    """Notification priority enum."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    geofence_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("geofences.id", ondelete="SET NULL"), nullable=True)
    
    # Notification content
    notification_type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Settings
    priority: Mapped[NotificationPriority] = mapped_column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)
    enable_sound: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Status
    status: Mapped[NotificationStatus] = mapped_column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    
    # Event context
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "geofence_enter", "geofence_exit"
    location_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # External IDs
    fcm_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    # Timestamps
    scheduled_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="notifications")
    geofence: Mapped["Geofence | None"] = relationship("Geofence")
    logs: Mapped[list["NotificationLog"]] = relationship("NotificationLog", back_populates="notification", cascade="all, delete-orphan")


class NotificationLog(Base):
    """Notification log for tracking delivery attempts."""
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notification_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Log details
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "sent", "delivered", "failed"
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamp
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    notification: Mapped["Notification"] = relationship("Notification", back_populates="logs")

