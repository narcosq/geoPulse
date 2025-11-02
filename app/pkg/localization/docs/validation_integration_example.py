"""Пример интеграции обработчика ошибок валидации с FastAPI."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.internal.pkg.middlewares.validation_error_handler import (
    create_validation_error_handlers,
    LocalizedValidationErrorHandler
)
from app.internal.pkg.middlewares.localization import LocalizationMiddleware


def setup_localized_validation_handlers(app: FastAPI):
    """
    Настроить локализованные обработчики ошибок валидации для FastAPI приложения.

    Args:
        app: Экземпляр FastAPI приложения
    """

    # 1. Добавить middleware для определения языка (должен быть первым)
    app.add_middleware(LocalizationMiddleware)

    # 2. Добавить middleware для обработки ошибок валидации
    app.add_middleware(LocalizedValidationErrorHandler)

    # 3. Альтернативно: добавить exception handlers
    # (используйте либо middleware, либо exception handlers, не оба одновременно)
    handlers = create_validation_error_handlers()
    for handler_config in handlers:
        app.add_exception_handler(
            handler_config["exception"],
            handler_config["handler"]
        )


# Пример использования в main.py
def create_app() -> FastAPI:
    """Создать FastAPI приложение с локализованными ошибками валидации."""

    app = FastAPI(
        title="Credit Core Service",
        description="Сервис кредитования с локализацией",
        version="1.0.0"
    )

    # Настроить локализованные обработчики ошибок
    setup_localized_validation_handlers(app)

    # Добавить роуты
    # app.include_router(calculator_router)

    return app


# Пример тестирования
async def test_localized_validation_errors():
    """Тестирование локализованных ошибок валидации."""
    from fastapi.testclient import TestClient

    app = create_app()
    client = TestClient(app)

    # Тест с неверным типом банка на английском
    response = client.get(
        "/api/v1/credit/calculator/product_conditions?bank_type=invalid&credit_type=credit",
        headers={"Accept-Language": "en-US"}
    )

    print("English validation error:")
    print(response.json())

    # Тест с неверным типом банка на кыргызском
    response = client.get(
        "/api/v1/credit/calculator/product_conditions?bank_type=invalid&credit_type=credit",
        headers={"Accept-Language": "ky"}
    )

    print("\\nKyrgyz validation error:")
    print(response.json())

    # Тест с неверным типом банка на русском
    response = client.get(
        "/api/v1/credit/calculator/product_conditions?bank_type=invalid&credit_type=credit",
        headers={"Accept-Language": "ru"}
    )

    print("\\nRussian validation error:")
    print(response.json())


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_localized_validation_errors())