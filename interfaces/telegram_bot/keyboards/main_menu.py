# interfaces/telegram_bot/keyboards/main_menu.py
"""
Главные клавиатуры меню с поддержкой локализации
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from ..localization.texts import t


def get_start_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Стартовое меню с кнопкой входа на остров
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t('btn_enter_island', lang),
                callback_data="enter_island"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_settings', lang),
                callback_data="settings"
            ),
            InlineKeyboardButton(
                text=t('btn_support', lang),
                callback_data="support"
            )
        ],
        [
            InlineKeyboardButton(
                text=t('btn_language', lang),
                callback_data="language"
            )
        ]
    ])

    return keyboard


def get_island_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Постоянное меню острова (нижние кнопки)
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t('btn_farm', lang)),
                KeyboardButton(text=t('btn_town', lang))
            ],
            [
                KeyboardButton(text=t('btn_citizen', lang)),
                KeyboardButton(text=t('btn_work', lang))
            ],
            [
                KeyboardButton(text=t('btn_inventory', lang)),
                KeyboardButton(text=t('btn_friends', lang))
            ],
            [
                KeyboardButton(text=t('btn_leaderboard', lang)),
                KeyboardButton(text=t('btn_other', lang))
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=t('menu_placeholder', lang),
        selective=False
    )

    return keyboard


def get_back_to_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t('btn_back', lang),
                callback_data="back_to_menu"
            )
        ]
    ])

    return keyboard
