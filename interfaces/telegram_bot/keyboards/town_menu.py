# interfaces/telegram_bot/keyboards/town_menu.py
"""
Клавиатуры для города
"""

import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..localization.texts import t

logger = logging.getLogger(__name__)


def get_town_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    """Меню города - 14 зданий в 2 колонки"""
    try:
        keyboard = [
            # Строка 1: Ратуша, Рынок
            [
                InlineKeyboardButton(text=t("btn_townhall", lang), callback_data="townhall"),
                InlineKeyboardButton(text=t("btn_market", lang), callback_data="market")
            ],
            # Строка 2: Академия, РяБанк
            [
                InlineKeyboardButton(text=t("btn_academy", lang), callback_data="academy"),
                InlineKeyboardButton(text=t("btn_ryabank", lang), callback_data="ryabank")
            ],
            # Строка 3: Товары, Ломбард
            [
                InlineKeyboardButton(text=t("btn_products", lang), callback_data="products"),
                InlineKeyboardButton(text=t("btn_pawnshop", lang), callback_data="pawnshop")
            ],
            # Строка 4: Таверна, Развлечения
            [
                InlineKeyboardButton(text=t("btn_tavern", lang), callback_data="tavern1"),
                InlineKeyboardButton(text=t("btn_entertainment", lang), callback_data="entertainment")
            ],
            # Строка 5: Недвижимость, Ветклиника
            [
                InlineKeyboardButton(text=t("btn_realestate", lang), callback_data="realestate"),
                InlineKeyboardButton(text=t("btn_vetclinic", lang), callback_data="vetclinic")
            ],
            # Строка 6: Стройка, Больница
            [
                InlineKeyboardButton(text=t("btn_construction", lang), callback_data="construction"),
                InlineKeyboardButton(text=t("btn_hospital", lang), callback_data="hospital")
            ],
            # Строка 7: Квантум-Хаб, Кладбище
            [
                InlineKeyboardButton(text=t("btn_quantumhub", lang), callback_data="quantumhub"),
                InlineKeyboardButton(text=t("btn_cemetery", lang), callback_data="cemetery")
            ]
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    except Exception as e:
        logger.error(f"Error creating town menu: {e}")
        # Fallback клавиатура
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏛️ Ратуша", callback_data="townhall"),
                    InlineKeyboardButton(text="🏪 Рынок", callback_data="market")
                ],
                [
                    InlineKeyboardButton(text="🎓 Академия", callback_data="academy"),
                    InlineKeyboardButton(text="🏦 РяБанк", callback_data="ryabank")
                ]
            ]
        )