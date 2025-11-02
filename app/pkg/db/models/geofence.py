"""Geofence model for defining geographic zones."""
from sqlalchemy import (
    BigInteger, String, Numeric, DateTime, Boolean, Text, JSON, Enum as SQLEnum, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.pkg.db.base import Base


class GeofenceType(str, enum.Enum):
    """Geofence type enum."""
    CIRCLE = "circle"
    POLYGON = "polygon"
    RECTANGLE = "rectangle"


class GeofenceStatus(str, enum.Enum):
    """Geofence status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Geofence(Base):
    """Geofence model for geographic zones."""
    __tablename__ = "geofences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Geofence type and coordinates
    geofence_type: Mapped[GeofenceType] = mapped_column(SQLEnum(GeofenceType), nullable=False)
    
    # For CIRCLE type
    center_latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    center_longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    radius_meters: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # For POLYGON type (stored as JSON array of [lat, lng] pairs)
    polygon_coordinates: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # For RECTANGLE type
    min_latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    max_latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    min_longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    max_longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    
    # Settings
    status: Mapped[GeofenceStatus] = mapped_column(SQLEnum(GeofenceStatus), default=GeofenceStatus.ACTIVE, nullable=False)
    notify_on_enter: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_exit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Notification settings
    notification_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    enable_sound: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_push: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_telegram: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    device_geofences: Mapped[list["DeviceGeofence"]] = relationship("DeviceGeofence", back_populates="geofence", cascade="all, delete-orphan")


class DeviceGeofence(Base):
    """Junction table for device-geofence relationships and tracking."""
    __tablename__ = "device_geofences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    geofence_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("geofences.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # State tracking
    is_inside: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_entered_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_exited_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    device: Mapped["Device"] = relationship("Device")
    geofence: Mapped["Geofence"] = relationship("Geofence", back_populates="device_geofences")

