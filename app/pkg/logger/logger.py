import json
import logging
import logging.config
from pathlib import Path
from typing import Optional, Dict, Any

from opentelemetry.instrumentation.logging import LoggingInstrumentor

from app.pkg.settings import settings
from .filters import CorrelationFilter


__all__ = ["get_logger"]


def _safe_load_config(path: Path) -> Optional[Dict[str, Any]]:
    """Загрузка конфигурации логгера из JSON с защитой от ошибок."""
    try:
        if path.exists():
            cfg = json.loads(path.read_text(encoding="utf-8"))

            for handler in cfg.get("handlers", {}).values():
                filename: Optional[str] = handler.get("filename")
                if filename:
                    Path(filename).parent.mkdir(parents=True, exist_ok=True)

            return cfg
    except Exception as e:
        logging.warning("Logger config load failed: %s", e)
    return None


def _fallback_basic_config() -> None:
    """Fallback-конфигурация, если dictConfig недоступен."""
    logging.basicConfig(
        level=logging.INFO,
        format=json.dumps({
            "time": "%(asctime)s",
            "logger": "%(name)s",
            "level": "%(levelname)s",
            "req_id": "%(request_id)s",
            "idem": "%(idempotency_key)s",
            "msg": "%(message)s",
        }),
    )


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает настроенный логгер с поддержкой Correlation ID.

    Features:
    - Загрузка dictConfig из settings.LOGGER.CONFIG_FILE.
    - Если конфиг невалидный → fallback на JSON structured logging.
    - Автоматическое создание папок для файловых логов.
    - CorrelationFilter вешается только на `app.*` логгеры.
    - Uvicorn/system логгеры не ломаются.
    """
    config_path = Path(settings.LOGGER.CONFIG_FILE)
    cfg = _safe_load_config(config_path)

    if cfg:
        try:
            logging.config.dictConfig(cfg)
        except Exception as e:
            logging.error("Logger dictConfig failed: %s", e)
            _fallback_basic_config()
    else:
        _fallback_basic_config()

    logger = logging.getLogger(name)

    # Добавляем CorrelationFilter только для бизнес-логгеров
    if name.startswith("app"):
        if not any(isinstance(f, CorrelationFilter) for f in logger.filters):
            logger.addFilter(CorrelationFilter())

        for handler in logger.handlers:
            if not any(isinstance(f, CorrelationFilter) for f in handler.filters):
                handler.addFilter(CorrelationFilter())

    LoggingInstrumentor().instrument(set_logging_format=True)

    return logger
