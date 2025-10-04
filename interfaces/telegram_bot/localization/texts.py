# interfaces/telegram_bot/localization/texts.py
"""
Система локализации с поддержкой RU/EN - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Кеш загруженных локалей
_locales_cache: Dict[str, Dict[str, str]] = {}

# Поддерживаемые языки
SUPPORTED_LANGUAGES = ['ru', 'en']
DEFAULT_LANGUAGE = 'ru'


def load_locale(lang_code: str) -> Dict[str, str]:
    """Загрузить тексты для языка"""
    if lang_code in _locales_cache:
        return _locales_cache[lang_code]

    try:
        if lang_code == 'ru':
            from .locales.ru import TEXTS
        elif lang_code == 'en':
            from .locales.en import TEXTS
        else:
            logger.warning(f"Язык {lang_code} не поддерживается, используем русский")
            from .locales.ru import TEXTS

        _locales_cache[lang_code] = TEXTS
        return TEXTS

    except ImportError as e:
        logger.error(f"Ошибка загрузки локали {lang_code}: {e}")
        # Fallback на русский
        from .locales.ru import TEXTS
        return TEXTS


def t(key: str, lang: str = 'ru', **kwargs) -> str:
    """
    Быстрая функция получения текста без async

    Args:
        key: Ключ текста
        lang: Код языка (ru, en)
        **kwargs: Параметры для форматирования

    Returns:
        Отформатированный текст
    """
    try:
        texts = load_locale(lang)
        text = texts.get(key, f"MISSING_{key}")

        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.error(f"Ошибка форматирования t({key}): {e}")

        return text

    except Exception as e:
        logger.error(f"Ошибка t({key}): {e}")
        return f"ERROR_{key}"


async def get_text(key: str, user_id: int, **kwargs) -> str:
    """
    Получить локализованный текст для пользователя БЕЗ рекурсии

    Args:
        key: Ключ текста
        user_id: ID пользователя в Telegram
        **kwargs: Параметры для форматирования

    Returns:
        Отформатированный текст
    """
    try:
        # Получаем язык пользователя НАПРЯМУЮ из БД без use cases
        from adapters.database.supabase.client import get_supabase_client

        client = await get_supabase_client()

        # Прямой запрос к БД для получения языка (избегаем рекурсии)
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["language"],
            filters={"user_id": user_id},
            single=True
        )

        lang = user_data['language'] if user_data else DEFAULT_LANGUAGE

        # Используем обычную функцию t()
        return t(key, lang, **kwargs)

    except Exception as e:
        logger.error(f"Ошибка получения текста {key} для пользователя {user_id}: {e}")
        # Fallback на русский
        return t(key, DEFAULT_LANGUAGE, **kwargs)
