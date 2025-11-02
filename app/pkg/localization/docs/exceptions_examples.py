"""Примеры использования локализованных исключений."""

from app.pkg.localization import Language
from app.pkg.models.exceptions.credit import (
    InvalidPrincipalException,
    InvalidProductException,
    InvalidMinPrincipalException,
    CreditConditionNotFoundException,
    InvalidDownPaymentException
)
from app.pkg.localization.docs.error_handler import (
    create_localized_credit_exception,
    raise_invalid_amount_error
)


def basic_localized_exception_example():
    """Базовый пример локализованного исключения."""
    try:
        # Поднять исключение на русском (по умолчанию)
        raise InvalidPrincipalException()
    except InvalidPrincipalException as e:
        print(f"RU Error: {e.detail['user_message']}")

    try:
        # Поднять исключение на кыргызском
        raise InvalidPrincipalException(language=Language.KY)
    except InvalidPrincipalException as e:
        print(f"KY Error: {e.detail['user_message']}")

    try:
        # Поднять исключение на английском
        raise InvalidPrincipalException(language=Language.EN)
    except InvalidPrincipalException as e:
        print(f"EN Error: {e.detail['user_message']}")


def exception_with_parameters_example():
    """Пример исключения с параметрами."""
    try:
        # Создать исключение с параметрами для перевода
        raise create_localized_credit_exception(
            InvalidProductException,
            Language.EN,
            max_amount=5000000,
            requested_amount=6000000
        )
    except InvalidProductException as e:
        print(f"Error with params: {e.detail['user_message']}")


def service_layer_exception_example():
    """Пример использования в сервисном слое."""

    def validate_credit_amount(amount: float, language: Language):
        """Проверить сумму кредита."""
        min_amount = 250000
        max_amount = 5000000

        if amount < min_amount:
            raise InvalidMinPrincipalException(
                language=language,
                translation_params={"min_amount": min_amount}
            )

        if amount > max_amount:
            raise InvalidProductException(
                language=language,
                translation_params={"max_amount": max_amount}
            )

    # Тестирование валидации
    for lang in [Language.RU, Language.KY, Language.EN]:
        try:
            validate_credit_amount(100000, lang)  # Слишком мало
        except InvalidMinPrincipalException as e:
            print(f"Min amount error ({lang.value}): {e.detail['user_message']}")

        try:
            validate_credit_amount(6000000, lang)  # Слишком много
        except InvalidProductException as e:
            print(f"Max amount error ({lang.value}): {e.detail['user_message']}")


def fastapi_integration_example():
    """Пример интеграции с FastAPI endpoint."""
    from fastapi import Request
    from app.internal.pkg.middlewares.localization import get_request_language

    class MockRequest:
        def __init__(self, accept_language: str):
            self.headers = {"Accept-Language": accept_language}
            self.state = type('State', (), {})()
            # Симуляция middleware
            language_code = accept_language.split(",")[0].split("-")[0].lower()
            language_mapping = {"ru": Language.RU, "ky": Language.KY, "en": Language.EN}
            self.state.language = language_mapping.get(language_code, Language.RU)

    def credit_calculation_endpoint(request, amount: float):
        """Симуляция FastAPI endpoint."""
        language = get_request_language(request)

        if amount < 250000:
            raise InvalidMinPrincipalException(
                language=language,
                translation_params={"min_amount": 250000}
            )

        return {"status": "success", "amount": amount}

    # Тестирование для разных языков
    test_cases = [
        ("ru", 100000),
        ("ky", 100000),
        ("en-US", 100000)
    ]

    for lang_header, amount in test_cases:
        mock_request = MockRequest(lang_header)
        try:
            result = credit_calculation_endpoint(mock_request, amount)
            print(f"Success ({lang_header}): {result}")
        except InvalidMinPrincipalException as e:
            print(f"Error ({lang_header}): {e.detail['user_message']}")


def middleware_error_handling_example():
    """Пример обработки ошибок в middleware."""
    from app.internal.pkg.middlewares.error_handler import LocalizedErrorHandlerMiddleware

    # Симуляция различных типов ошибок
    def simulate_credit_service_errors():
        """Симулировать различные ошибки кредитного сервиса."""

        # Кредитные условия не найдены
        try:
            raise CreditConditionNotFoundException(language=Language.EN)
        except CreditConditionNotFoundException as e:
            print(f"Condition not found: {e.detail}")

        # Неверный первоначальный взнос
        try:
            raise InvalidDownPaymentException(
                language=Language.KY,
                translation_params={"max_down_payment": 50}
            )
        except InvalidDownPaymentException as e:
            print(f"Invalid down payment: {e.detail}")

    simulate_credit_service_errors()


def error_response_structure_example():
    """Пример структуры ответа об ошибке."""
    try:
        raise InvalidPrincipalException(
            language=Language.EN,
            code=40601,
            trace_id="req-123-456-789"
        )
    except InvalidPrincipalException as e:
        print("Error response structure:")
        print(f"  Status code: {e.status_code}")
        print(f"  Detail: {e.detail}")
        print(f"  Outcome: {e.detail['outcome']}")
        print(f"  Code: {e.detail['code']}")
        print(f"  User message: {e.detail['user_message']}")
        print(f"  Developer message: {e.detail['developer_message']}")
        print(f"  Trace ID: {e.detail['trace_id']}")


if __name__ == "__main__":
    print("=== Базовые локализованные исключения ===")
    basic_localized_exception_example()

    print("\\n=== Исключения с параметрами ===")
    exception_with_parameters_example()

    print("\\n=== Использование в сервисном слое ===")
    service_layer_exception_example()

    print("\\n=== Интеграция с FastAPI ===")
    fastapi_integration_example()

    print("\\n=== Обработка ошибок в middleware ===")
    middleware_error_handling_example()

    print("\\n=== Структура ответа об ошибке ===")
    error_response_structure_example()