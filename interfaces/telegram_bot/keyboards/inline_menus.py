# interfaces/telegram_bot/keyboards/inline_menus.py
"""
Inline клавиатуры с локализацией
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.texts import (
    BTN_CHANGE_LANGUAGE,
    BTN_NOTIFICATIONS,
    BTN_CHANGE_CHARACTER,
)



def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    keyboard = [
        [InlineKeyboardButton(text="🌐 Изменить язык", callback_data="change_language")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications")],
        [InlineKeyboardButton(text="🎭 Изменить персонажа", callback_data="change_character")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    keyboard = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def get_language_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Выбор языка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data="lang_ru"
            ),
            InlineKeyboardButton(
                text="🇬🇧 English",
                callback_data="lang_en"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_back', lang),
                callback_data="settings"
            )
        ]
    ])

    return keyboard


def get_profile_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Меню профиля"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t('btn_detailed_stats', lang),
                callback_data="detailed_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_achievements', lang),
                callback_data="achievements"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_back', lang),
                callback_data="back_to_start"
            )
        ]
    ])

    return keyboard


def get_other_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Меню 'Прочее'"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t('btn_settings', lang),
                callback_data="settings"
            ),
            InlineKeyboardButton(
                text=t('btn_profile', lang),
                callback_data="profile"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_support', lang),
                callback_data="support"
            ),
            InlineKeyboardButton(
                text=t('btn_help', lang),
                callback_data="help"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_promo', lang),
                callback_data="promo"
            ),
            InlineKeyboardButton(
                text=t('btn_quantum_pass', lang),
                callback_data="quantum_pass"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_back', lang),
                callback_data="back_to_menu"
            )
        ]
    ])

    return keyboard
