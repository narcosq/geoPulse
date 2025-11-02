from starlette import status

from app.pkg.models.base import BaseAPIException

__all__ = [
    "InvalidCredentials",
    "NotFound",
    "ValidationError",
    "InternalServerError",
]


class InvalidCredentials(BaseAPIException):
    default_message = "Could not validate credentials."
    default_user_message = "Неверные учетные данные"
    default_developer_message = "Invalid credentials"
    default_status_code = status.HTTP_403_FORBIDDEN
    default_code = 40301


class NotFound(BaseAPIException):
    default_message = "Resource not found."
    default_user_message = "Ресурс не найден"
    default_developer_message = "Not found"
    default_status_code = status.HTTP_404_NOT_FOUND
    default_code = 40401


class ValidationError(BaseAPIException):
    default_message = "Validation failed."
    default_user_message = "Ошибка валидации входных данных"
    default_developer_message = "Validation failed on multiple fields"
    default_status_code = status.HTTP_400_BAD_REQUEST
    default_code = 40001


class InternalServerError(BaseAPIException):
    default_message = "Internal server error"
    default_user_message = "Внутренняя ошибка сервера"
    default_developer_message = "Internal server error"
    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 50000
