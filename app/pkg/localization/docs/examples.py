"""Примеры использования локализации."""

from app.pkg.localization import get_translator, Language


def basic_translation_example():
    """Базовый пример использования переводов."""
    translator = get_translator()

    # Перевод на русский (по умолчанию)
    title_ru = translator.t("credit.calculator.title")
    print(f"RU: {title_ru}")  # "Кредитный калькулятор"

    # Перевод на кыргызский
    title_ky = translator.t("credit.calculator.title", Language.KY)
    print(f"KY: {title_ky}")  # "Кредит калькулятору"

    # Перевод на английский
    title_en = translator.t("credit.calculator.title", Language.EN)
    print(f"EN: {title_en}")  # "Credit Calculator"


def translation_with_parameters_example():
    """Пример перевода с параметрами."""
    translator = get_translator()

    # Перевод с параметрами
    min_value_ru = translator.t("validation.min_value", Language.RU, min=250000)
    print(f"RU: {min_value_ru}")  # "Минимальное значение: 250000"

    min_value_en = translator.t("validation.min_value", Language.EN, min=250000)
    print(f"EN: {min_value_en}")  # "Minimum value: 250000"


def credit_status_translation_example():
    """Пример перевода статусов кредита."""
    translator = get_translator()

    statuses = ["approved", "rejected", "pending"]

    for status in statuses:
        key = f"credit.status.{status}"
        ru = translator.t(key, Language.RU)
        ky = translator.t(key, Language.KY)
        en = translator.t(key, Language.EN)

        print(f"{status}: RU='{ru}', KY='{ky}', EN='{en}'")


def fastapi_integration_example():
    """Пример интеграции с FastAPI."""
    from fastapi import Request
    from app.internal.pkg.middlewares.localization import get_request_language
    from app.pkg.models.schemas.calculator import CreditCalculatorResponse

    # Симуляция FastAPI request с языком
    class MockRequest:
        def __init__(self, accept_language: str):
            self.headers = {"Accept-Language": accept_language}
            self.state = type('State', (), {})()

    # Пример для разных языков
    for lang_header in ["ru", "ky", "en-US"]:
        mock_request = MockRequest(lang_header)

        # Middleware определит язык
        from app.internal.pkg.middlewares.localization import LocalizationMiddleware
        middleware = LocalizationMiddleware(None)

        # Определяем язык из заголовка
        language_code = lang_header.split(",")[0].split("-")[0].split(";")[0].lower()
        language_mapping = {
            "ru": Language.RU,
            "ky": Language.KY,
            "en": Language.EN,
        }
        language = language_mapping.get(language_code, Language.RU)
        mock_request.state.language = language

        # Получаем локализованную схему
        schema = CreditCalculatorResponse.localized_schema(language)

        print(f"\\nLanguage: {language.value}")
        print(f"Amount field description: {schema['properties']['amount']['description']}")
        print(f"Term field description: {schema['properties']['term_months']['description']}")


def error_message_translation_example():
    """Пример перевода сообщений об ошибках."""
    translator = get_translator()

    error_keys = [
        "errors.not_found",
        "errors.validation_failed",
        "errors.unauthorized"
    ]

    print("Error messages in different languages:")
    for key in error_keys:
        ru = translator.t(key, Language.RU)
        ky = translator.t(key, Language.KY)
        en = translator.t(key, Language.EN)

        print(f"  {key}:")
        print(f"    RU: {ru}")
        print(f"    KY: {ky}")
        print(f"    EN: {en}")


if __name__ == "__main__":
    print("=== Базовый пример переводов ===")
    basic_translation_example()

    print("\\n=== Переводы с параметрами ===")
    translation_with_parameters_example()

    print("\\n=== Переводы статусов кредита ===")
    credit_status_translation_example()

    print("\\n=== Интеграция с FastAPI ===")
    fastapi_integration_example()

    print("\\n=== Сообщения об ошибках ===")
    error_message_translation_example()