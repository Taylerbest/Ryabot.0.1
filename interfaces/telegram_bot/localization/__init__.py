# interfaces/telegram_bot/localization/__init__.py
"""
Локализация бота
"""

from .texts import t, get_text, load_locale

__all__ = ['t', 'get_text', 'load_locale']
