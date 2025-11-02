"""Location model for tracking device positions."""
from sqlalchemy import (
    BigInteger, Numeric, DateTime, ForeignKey, String, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.pkg.db.base import Base


class Location(Base):
    """Location model for device positions."""
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Coordinates
    latitude: Mapped[float] = mapped_column(Numeric(10, 8), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(11, 8), nullable=False)
    altitude: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Location metadata
    accuracy: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    speed: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    heading: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Address information (can be reverse geocoded)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Timestamp
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="locations")

    # Indexes for efficient geospatial queries
    __table_args__ = (
        Index("idx_location_device_timestamp", "device_id", "timestamp"),
        Index("idx_location_coordinates", "latitude", "longitude"),
    )

