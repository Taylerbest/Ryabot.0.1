# interfaces/telegram_bot/keyboards/__init__.py
"""
Клавиатуры для Telegram бота
"""

from .main_menu import get_start_menu, get_island_menu
from .inline_menus import get_settings_keyboard, get_language_keyboard

__all__ = [
    'get_start_menu',
    'get_island_menu',
    'get_settings_keyboard',
    'get_language_keyboard'
]
