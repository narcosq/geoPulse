# base
## Описание проекта / Project Description

**base** - микросервис 

### Основные функции:
- 

### Архитектурные принципы:
- **Разделение ответственности**: Четкое разделение между бизнес-логикой (`internal`) и общими утилитами (`pkg`)
- **Внедрение зависимостей**: Использование контейнеров для управления зависимостями
- **Event-Driven Architecture**: Асинхронная обработка событий через Kafka для интеграции между сервисами
- **Наблюдаемость**: Полная интеграция с OpenTelemetry для трассировки и мониторинга
- **Асинхронность**: Асинхронная обработка запросов и фоновые задачи

## Development Commands

### Running the Application
```bash
# Run the development server with auto-reload
make run
# Alternative: uvicorn app:create_app --host 0.0.0.0 --reload --port 8000

# Run with Docker
make docker_up
```

### Code Quality and Formatting
```bash
# Format code (runs isort, black, docformatter, add-trailing-comma)
make fmt

# Check code quality (runs flake8, black_check, docformatter_check, safety, bandit)
make check

# Individual tools
make black          # Format with black
make isort          # Sort imports
make flake8         # Lint with flake8
make mypy           # Type checking
make safety         # Security vulnerability check
make bandit         # Security analysis
```

### Database Operations
```bash
# Run migrations
make migrate

# Create new migration
make migrate-create message="your migration message"

# Rollback migrations
make migrate-rollback

# Reload migrations
make migrate-reload
```

### Dependencies
```bash
# Install production dependencies
make install-deps

# Install development dependencies
make install-dev-deps

# Compile requirements
make deps           # Compile requirements.txt
make dev-deps       # Compile dev-requirements.txt
```

### Background Tasks
```bash
# Run celery worker
make run_worker

# Run celery beat scheduler
make run_beat
```

## Architecture Overview

### Core Structure
This is a FastAPI-based credit core service with dependency injection architecture:

- **FastAPI Application**: Created via `create_app()` factory in `app/__init__.py`
- **Dependency Injection**: Uses `dependency-injector` library with container-based architecture
- **Clean Architecture**: Separated into internal (business logic) and pkg (shared utilities) layers

### Key Components

#### Dependency Injection System
- **Containers**: Defined in `app/pkg/models/core/containers.py`
- **Main Containers**: `__containers__` for web app, `__task_containers__` for background tasks
- **Wiring**: Automatically wires dependencies to FastAPI app via `__containers__.wire_packages(app=app)`

#### Application Layers
- **`app/internal/`**: Business logic, routes, repositories, services
- **`app/pkg/`**: Shared utilities, models, connectors, clients
- **`app/configuration/`**: Server setup, dependency container configuration

#### Database & Storage
- **PostgreSQL**: Primary database with SQLAlchemy ORM
- **Redis**: Caching layer
- **Alembic**: Database migrations (via custom `scripts/migrate.py`)

#### Observability
- **OpenTelemetry**: Full observability stack with traces, metrics, logs
- **Jaeger**: Distributed tracing backend
- **OTEL Collector**: Telemetry data collection and export

### Server Configuration
The `Server` class in `app/configuration/server.py` handles:
- Route registration from `app.internal.routes.__routes__`
- Middleware setup (CORS, correlation, exception handling)
- OpenTelemetry tracing initialization
- HTTP exception handlers for `BaseAPIException` and `RequestValidationError`

### Settings & Configuration
- Uses `pydantic-settings` for configuration management
- Settings accessible via `app.pkg.settings.settings`
- Environment-based configuration with `.env` file support

## Project Technology Stack
- **Framework**: FastAPI with Uvicorn
- **Database**: PostgreSQL with AsyncPG driver
- **ORM**: SQLAlchemy 2.0
- **Caching**: Redis
- **Message Broker**: Kafka with aiokafka
- **Background Tasks**: Celery
- **Observability**: OpenTelemetry + Jaeger
- **Dependency Management**: Poetry
- **Code Quality**: Black, isort, flake8, mypy, bandit, safety


## 🎯 Полная настройка Babel

1. babel.cfg - конфигурация для извлечения строк из кода
2. setup.cfg - настройки команд babel
3. translator.py - обновлен для поддержки .po/.mo файлов
4. Makefile - удобные команды для работы с переводами

🔧 Доступные команды

# Показать справку
make babel-help

# Извлечь строки для перевода из кода
make extract-messages

# Создать .po файлы для новых языков
make init-catalogs

# Обновить существующие переводы
make update-catalogs

# Скомпилировать .po в .mo файлы
make compile-catalogs

# Проверить статус переводов
make translations-status

# Полный workflow
make setup-translations    # для новых переводов
make update-translations   # для обновления существующих

🚀 Как использовать

1. Извлечение переводимых строк:
make extract-messages
2. Создание каталогов переводов:
make init-catalogs
3. Редактирование .po файлов в app/pkg/localization/locales/{lang}/LC_MESSAGES/messages.po
4. Компиляция переводов:
make compile-catalogs

📁 Структура файлов

app/pkg/localization/locales/
├── messages.pot          # Шаблон переводов
├── ru/LC_MESSAGES/
│   ├── messages.po       # Исходный файл переводов
│   └── messages.mo       # Скомпилированный файл
├── ky/LC_MESSAGES/
│   ├── messages.po
│   └── messages.mo
└── en/LC_MESSAGES/
  ├── messages.po
  └── messages.mo
