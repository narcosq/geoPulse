import logging

logger = logging.getLogger(__name__)


def _optional_import(module_name: str, class_name: str):
    """
    Пытается импортировать класс из модуля.
    Если модуль отсутствует → возвращает None и пишет warning.
    """
    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except ImportError:
        logger.warning("Instrumentation %s.%s is not available", module_name, class_name)
        return None
