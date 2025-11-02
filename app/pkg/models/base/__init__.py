"""Base business models.

All models *must* be inherited by them.
"""

from .enum import BaseEnum
from .exception import BaseAPIException, LocalizedAPIException
from .model import BaseModel, Model
