from starlette import status

from app.pkg.models.base import BaseAPIException

__all__ = ["InvalidCredentials"]


class InvalidCredentials(BaseAPIException):
    default_message = "Could not validate credentials."
    default_user_message = "Неверные учетные данные"
    default_developer_message = "Invalid credentials"
    default_status_code = status.HTTP_403_FORBIDDEN
    default_code = 40301
