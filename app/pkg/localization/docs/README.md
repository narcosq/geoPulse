# Локализация

Система локализации поддерживает многоязычность для API ответов и документации.

## Поддерживаемые языки

- **ru** - Русский (по умолчанию)
- **ky** - Кыргызский
- **en** - Английский

## Структура

```
app/pkg/localization/
├── __init__.py          # Экспорт основных компонентов
├── models.py            # Enum поддерживаемых языков
├── translator.py        # Основной класс переводчика
├── examples.py          # Примеры использования
└── locales/             # Файлы переводов
    ├── ru.json          # Русский
    ├── ky.json          # Кыргызский
    └── en.json          # Английский
```

## Использование

### Базовый перевод

```python
from app.pkg.localization import get_translator, Language

translator = get_translator()

# Перевод на русский (по умолчанию)
title = translator.t("credit.calculator.title")  # "Кредитный калькулятор"

# Перевод на другие языки
title_ky = translator.t("credit.calculator.title", Language.KY)  # "Кредит калькулятору"
title_en = translator.t("credit.calculator.title", Language.EN)  # "Credit Calculator"
```

### Перевод с параметрами

```python
# С параметрами
error = translator.t("validation.min_value", Language.EN, min=250000)
# Результат: "Minimum value: 250000"
```

### Интеграция с FastAPI

#### 1. Middleware для определения языка

```python
# app/internal/pkg/middlewares/localization.py
from app.internal.pkg.middlewares.localization import LocalizationMiddleware

# Добавить в FastAPI app
app.add_middleware(LocalizationMiddleware)
```

Middleware автоматически определяет язык из заголовка `Accept-Language`:
- `Accept-Language: ru` → Русский
- `Accept-Language: ky` → Кыргызский
- `Accept-Language: en-US` → Английский

#### 2. Использование в роутах

```python
from fastapi import Request
from app.internal.pkg.middlewares.localization import get_request_language

@router.post("/calculate")
async def calculate_credit(
    calc_request: CreditCalculatorRequest,
    request: Request
):
    # Получить язык пользователя
    language = get_request_language(request)

    # Использовать для переводов
    translator = get_translator()
    message = translator.t("credit.calculator.description", language)

    return result
```

#### 3. Локализованные схемы

Schemas наследуются от `LocalizedResponse` для автоматического перевода описаний полей:

```python
from app.pkg.models.schemas.localized import LocalizedResponse, localized_field

class CreditCalculatorResponse(LocalizedResponse):
    amount: Decimal = localized_field("credit.calculator.amount", ge=250_000)
    term_months: int = localized_field("credit.calculator.term_months", ge=3)

# Получить схему с переводами
schema = CreditCalculatorResponse.localized_schema(Language.EN)
```

## Структура файлов переводов

Файлы JSON организованы иерархически:

```json
{
  "credit": {
    "calculator": {
      "title": "Кредитный калькулятор",
      "amount": "Сумма кредита",
      "term_months": "Срок кредита в месяцах"
    },
    "status": {
      "approved": "Одобрено",
      "rejected": "Отклонено"
    }
  },
  "validation": {
    "required": "Поле обязательно для заполнения",
    "min_value": "Минимальное значение: {min}"
  }
}
```

## Добавление новых переводов

1. **Добавить ключи в файлы локализации:**

```json
// ru.json
{
  "new_feature": {
    "title": "Новая функция",
    "description": "Описание новой функции"
  }
}

// ky.json
{
  "new_feature": {
    "title": "Жаңы функция",
    "description": "Жаңы функциянын описания"
  }
}

// en.json
{
  "new_feature": {
    "title": "New Feature",
    "description": "Description of new feature"
  }
}
```

2. **Использовать в коде:**

```python
title = translator.t("new_feature.title", language)
```

## Примеры

Запустить примеры использования:

```bash
python -m app.pkg.localization.examples
```

## Особенности

1. **Fallback**: Если перевод не найден для выбранного языка, система возвращает русский вариант
2. **Вложенные ключи**: Поддерживается навигация по вложенным объектам через точку
3. **Форматирование**: Строки поддерживают форматирование с параметрами `{parameter}`
4. **Автоматическое определение языка**: Middleware автоматически парсит заголовок `Accept-Language`

## Babel интеграция

Для извлечения строк для перевода используется Babel:

```bash
# Извлечь строки для перевода
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .

# Создать файл перевода для нового языка
pybabel init -i messages.pot -d translations -l de

# Обновить существующие переводы
pybabel update -i messages.pot -d translations
```