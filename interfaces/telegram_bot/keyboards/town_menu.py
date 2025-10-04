# interfaces/telegram_bot/keyboards/town_menu.py
"""
Клавиатура меню Города с локализацией
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..localization.texts import t


def get_town_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Меню города с 14 зданиями в оригинальной раскладке 2x7
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t('btn_townhall', lang), callback_data="townhall"),
            InlineKeyboardButton(text=t('btn_market', lang), callback_data="market")
        ],
        [
            InlineKeyboardButton(text=t('btn_ryabank', lang), callback_data="ryabank"),
            InlineKeyboardButton(text=t('btn_products', lang), callback_data="products")
        ],
        [
            InlineKeyboardButton(text=t('btn_pawnshop', lang), callback_data="pawnshop"),
            InlineKeyboardButton(text=t('btn_tavern', lang), callback_data="tavern1")
        ],
        [
            InlineKeyboardButton(text=t('btn_academy', lang), callback_data="academy"),
            InlineKeyboardButton(text=t('btn_entertainment', lang), callback_data="entertainment")
        ],
        [
            InlineKeyboardButton(text=t('btn_realestate', lang), callback_data="realestate"),
            InlineKeyboardButton(text=t('btn_vetclinic', lang), callback_data="vetclinic")
        ],
        [
            InlineKeyboardButton(text=t('btn_construction', lang), callback_data="construction"),
            InlineKeyboardButton(text=t('btn_hospital', lang), callback_data="hospital")
        ],
        [
            InlineKeyboardButton(text=t('btn_quantumhub', lang), callback_data="quantumhub"),
            InlineKeyboardButton(text=t('btn_cemetery', lang), callback_data="cemetery")
        ],
    ])

    return keyboard
