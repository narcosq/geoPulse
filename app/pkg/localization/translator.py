"""Translator implementation using Babel."""

from pathlib import Path
from typing import Dict, Optional

from babel.support import Translations

from .models import Language


class Translator:
    """Translation handler using Babel .po/.mo files."""

    def __init__(self, locales_dir: str = None):
        """Initialize translator."""
        if locales_dir is None:
            current_dir = Path(__file__).parent
            locales_dir = current_dir / "locales"

        self.locales_dir = Path(locales_dir)
        self._babel_translations: Dict[str, Translations] = {}
        self._load_babel_translations()

    def _load_babel_translations(self):
        """Load Babel .po/.mo translation files."""
        if not self.locales_dir.exists():
            return

        for lang in Language:
            try:
                # Загружаем переводы из .mo файлов
                translation = Translations.load(
                    dirname=str(self.locales_dir),
                    locales=[lang.value],
                    domain='messages'
                )
                if translation:
                    self._babel_translations[lang.value] = translation
            except Exception:
                # Если не найдены .mo файлы, продолжаем без этого языка
                pass

    def translate(self, key: str, language: Language = Language.RU, **kwargs) -> str:
        """Translate a key to the specified language."""
        babel_translation = self._babel_translations.get(language.value)

        if not babel_translation:
            # Fallback к русскому, если нет переводов для языка
            if language != Language.RU:
                return self.translate(key, Language.RU, **kwargs)
            # Если и русского нет, возвращаем ключ
            return key

        # Получить перевод из babel
        translated = babel_translation.gettext(key)

        # Если перевод не найден, пробуем fallback к русскому
        if translated == key and language != Language.RU:
            return self.translate(key, Language.RU, **kwargs)

        # Форматировать с параметрами если есть
        if kwargs:
            try:
                return translated.format(**kwargs)
            except (KeyError, ValueError):
                return translated

        return translated

    def t(self, key: str, language: Language = Language.RU, **kwargs) -> str:
        """Short alias for translate method."""
        return self.translate(key, language, **kwargs)


# Global translator instance
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Get global translator instance."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator