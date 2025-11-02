ifneq ("$(wildcard .env)","")
  include .env
  export
else
endif


# enumeration of * .py files storage or folders is required.
files_to_fmt 	?= app
files_to_check 	?= app

message ?= new migration
API_SERVER_PORT ?= 8000

## Default target
.DEFAULT_GOAL := run

PROJECT_NAME = $(shell basename $(PWD))
CELERY_SCHEDULE_DB ?= django_celery_beat.schedulers:DatabaseScheduler

## Build api docker containers
docker_up:
	docker-compose up --build -d

run:
	uvicorn app:create_app --host 0.0.0.0 --reload --port ${API_SERVER_PORT}

run_worker:
	celery -A tasks.celery_app worker --pool solo -l info

run_beat:
	celery -A tasks.celery_app beat -l info

pyenv:
	echo $(PROJECT_NAME) > .python-version && pyenv install -s 3.12.4 && pyenv virtualenv -f 3.12.4 $(PROJECT_NAME)

pyenv-delete:
	pyenv virtualenv-delete -f $(PROJECT_NAME)

install-dev-deps: dev-deps
	pip-sync requirements.txt dev-requirements.txt

install-deps: deps
	pip-sync requirements.txt

deps:
	pip install --upgrade pip pip-tools
	pip-compile --output-file requirements.txt --resolver=backtracking pyproject.toml

dev-deps: deps
	pip-compile --extra=dev --output-file dev-requirements.txt --resolver=backtracking pyproject.toml

## Format all
fmt: format
format: isort black docformatter add-trailing-comma


## Check code quality
chk: check
lint: check
check: flake8 black_check docformatter_check safety bandit

## Migrate database
migrate:
	poetry run alembic -c ./config/alembic.ini upgrade head

## Rollback migrations in database
migrate-rollback:
	poetry run alembic -c ./config/alembic.ini downgrade -1

## Create migration
migrate-create:
	poetry run alembic -c ./config/alembic.ini revision --autogenerate -m "$(message)"

## Migrate database
yoyo-migrate:
	python -m scripts.migrate

## Rollback migrations in database
yoyo-migrate-rollback:
	python -m scripts.migrate --rollback --config ./config/yoyo.ini

yoyo-migrate-reload:
	python -m scripts.migrate --reload --config ./config/yoyo.ini

## Create migration
yoyo-migrate-create:
	python -m yoyo new --config ./config/yoyo.ini --message "$(message)"

## Sort imports
isort:
	isort ${files_to_fmt}


## Format code
black:
	black ${files_to_fmt}


## Check code formatting
black_check:
	black --check ${files_to_check}


## Format docstring PEP 257
docformatter:
	docformatter -ir ${files_to_fmt}


## Check docstring formatting
docformatter_check:
	docformatter -cr ${files_to_check}


## Check pep8
flake8:
	flake8 ${files_to_check} --config ./config/setup.cfg


## Check typing
mypy:
	mypy ${files_to_check} --config ./config/setup.cfg


## Check if all dependencies are secure and do not have any known vulnerabilities
safety:
	safety check --full-report


## Check code security
bandit:
	bandit -r ${files_to_check} -x app

## Add trailing comma works only on unix.
# an error is expected on windows.
add-trailing-comma:
	find app server -name "*.py" -exec add-trailing-comma '{}' --py36-plus \;

# ================================
# Команды для работы с переводами
# ================================

# Переменные для переводов
LOCALES_DIR = app/pkg/localization/locales
MESSAGES_POT = $(LOCALES_DIR)/messages.pot
LANGUAGES = ru ky en

.PHONY: babel-help extract-messages init-catalogs update-catalogs compile-catalogs clean-translations translations-status sync-translations

babel-help:
	@echo "Доступные команды для работы с переводами:"
	@echo ""
	@echo "  extract-messages    - Извлечь все строки для перевода из кода"
	@echo "  init-catalogs       - Создать новые .po файлы для всех языков"
	@echo "  update-catalogs     - Обновить существующие .po файлы"
	@echo "  compile-catalogs    - Скомпилировать .po файлы в .mo"
	@echo "  clean-translations  - Удалить скомпилированные .mo файлы"
	@echo "  translations-status - Показать статус переводов"
	@echo ""
	@echo "Полный workflow:"
	@echo "  1. make extract-messages"
	@echo "  2. make init-catalogs (только для новых языков)"
	@echo "  3. make update-catalogs"
	@echo "  4. Отредактировать .po файлы"
	@echo "  5. make compile-catalogs"

# Извлечение строк для перевода
extract-messages:
	@echo "Извлекаем строки для перевода..."
	pybabel extract -F config/babel.cfg -k "t" -k "translator.t" -o $(MESSAGES_POT) .
	@echo "Файл $(MESSAGES_POT) создан/обновлен"

# Создание новых каталогов переводов
init-catalogs:
	@echo "Создаем каталоги переводов для языков: $(LANGUAGES)"
	@for lang in $(LANGUAGES); do \
		echo "Создаем каталог для языка: $$lang"; \
		pybabel init -i $(MESSAGES_POT) -d $(LOCALES_DIR) -l $$lang; \
	done

# Обновление существующих каталогов
update-catalogs:
	@echo "Обновляем каталоги переводов..."
	@for lang in $(LANGUAGES); do \
		echo "Обновляем каталог для языка: $$lang"; \
		pybabel update -i $(MESSAGES_POT) -d $(LOCALES_DIR) -l $$lang; \
	done

# Компиляция переводов
compile-catalogs:
	@echo "Компилируем переводы..."
	pybabel compile -d $(LOCALES_DIR)
	@echo "Переводы скомпилированы в .mo файлы"

# Очистка скомпилированных файлов
clean-translations:
	@echo "Удаляем скомпилированные .mo файлы..."
	find $(LOCALES_DIR) -name "*.mo" -delete
	@echo "Файлы .mo удалены"

# Проверка статуса переводов
translations-status:
	@echo "Статус переводов:"
	@for lang in $(LANGUAGES); do \
		echo ""; \
		echo "=== Язык: $$lang ==="; \
		if [ -f "$(LOCALES_DIR)/$$lang/LC_MESSAGES/messages.po" ]; then \
			echo "Файл .po существует"; \
			msgfmt --statistics $(LOCALES_DIR)/$$lang/LC_MESSAGES/messages.po 2>/dev/null || echo "Ошибка при проверке статистики"; \
		else \
			echo "Файл .po не найден"; \
		fi; \
		if [ -f "$(LOCALES_DIR)/$$lang/LC_MESSAGES/messages.mo" ]; then \
			echo "Файл .mo существует"; \
		else \
			echo "Файл .mo не найден"; \
		fi; \
	done

# Полный workflow для новых переводов
setup-translations: extract-messages init-catalogs
	@echo "Переводы настроены. Теперь отредактируйте .po файлы и выполните 'make compile-catalogs'"

# Синхронизация переводов из JSON в .po файлы
sync-translations:
	@echo "Синхронизируем переводы из JSON в .po файлы..."
	python scripts/sync_translations.py

# Обновление существующих переводов
update-translations: extract-messages update-catalogs
	@echo "Переводы обновлены. Теперь отредактируйте .po файлы и выполните 'make compile-catalogs'"

# Полный цикл: синхронизация JSON -> .po -> .mo
full-sync: sync-translations compile-catalogs
	@echo "Полная синхронизация завершена!"
