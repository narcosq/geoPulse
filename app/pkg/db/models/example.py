from sqlalchemy import (
    BigInteger, Numeric, Integer, DateTime, Boolean,
    Enum as SQLEnum, String, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.pkg.db.base import Base


class Example(Base):
    """Таблица примеров."""
    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
