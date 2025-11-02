from pydantic import Field, conint
from typing import Generic, List, TypeVar

from app.pkg.models.base import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: conint(ge=1) = Field(default=1)
    limit: conint(ge=1, le=100) = Field(default=20)


class PaginatedResponse(BaseModel, Generic[T]):
    outcome: str = "success"
    data: List[T]
    page: int
    limit: int
    total: int
