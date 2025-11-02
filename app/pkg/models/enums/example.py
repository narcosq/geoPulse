"""Example domain enums."""

from enum import Enum


class ExampleStatus(str, Enum):
    """Example application status."""
    DRAFT = "draft"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
