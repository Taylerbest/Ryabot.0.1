# interfaces/telegram_bot/handlers/leaderboard.py
"""
Handler меню лидерборда
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *

router = Router()
logger = logging.getLogger(__name__)


def get_leaderboard_keyboard():
    """Клавиатура лидерборда - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_LEADERS_FARM, callback_data="leaders_farm"),
         InlineKeyboardButton(text=BTN_LEADERS_WORK, callback_data="leaders_work"),
         InlineKeyboardButton(text=BTN_LEADERS_TRADE, callback_data="leaders_trade")],
        [InlineKeyboardButton(text=BTN_LEADERS_EXPEDITION, callback_data="leaders_expedition"),
         InlineKeyboardButton(text=BTN_LEADERS_GAMBLING, callback_data="leaders_gambling"),
         InlineKeyboardButton(text=BTN_LEADERS_FIGHT, callback_data="leaders_fight")],
        [InlineKeyboardButton(text=BTN_LEADERS_RACING, callback_data="leaders_racing"),
         InlineKeyboardButton(text=BTN_LEADERS_RBTC, callback_data="leaders_rbtc"),
         InlineKeyboardButton(text=BTN_LEADERS_PARTNER, callback_data="leaders_partner")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_leaderboard_data() -> dict:
    """Получить данные лидеров"""
    # TODO: Получать реальные данные из БД
    return {
        "top_farmer": "—",
        "top_employer": "—",
        "top_trader": "—",
        "top_explorer": "—",
        "top_gambler": "—",
        "top_fighter": "—",
        "top_racer": "—",
        "top_rbtc": "—",
        "top_partner": "—"
    }


async def show_leaderboard_menu(message: Message):
    """Показать меню лидерборда"""
    try:
        leaders_data = await get_leaderboard_data()
        leaders_text = LEADERBOARD_MENU.format(**leaders_data)

        await message.answer(
            leaders_text,
            reply_markup=get_leaderboard_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка меню лидерборда: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИКИ РЕЙТИНГОВ ===

@router.callback_query(F.data.startswith("leaders_"))
async def handle_leaderboard(callback: CallbackQuery):
    """Обработка рейтингов"""
    try:
        category = callback.data.split("_")[1]

        category_names = {
            "farm": "🏡 ТОП 50 ФЕРМЕРОВ",
            "work": "💼 ТОП 50 РАБОТОДАТЕЛЕЙ",
            "trade": "⚖️ ТОП 50 ТОРГОВЦЕВ",
            "expedition": "🏕 ТОП 50 ИССЛЕДОВАТЕЛЕЙ",
            "gambling": "🎲 ТОП 50 АЗАРТНИКОВ",
            "fight": "🥊 ТОП 50 БОЙЦОВ",
            "racing": "🏇 ТОП 50 ГОНЩИКОВ",
            "rbtc": "💠 ТОП 50 СЖИГАТЕЛЕЙ",
            "partner": "🤝 ТОП 50 ПАРТНЕРОВ"
        }

        category_name = category_names.get(category, "ТОП 50")

        await callback.message.edit_text(
            f"{category_name}\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_leaderboard")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка рейтинга: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_leaderboard")
async def back_to_leaderboard(callback: CallbackQuery):
    """Возврат в меню лидерборда"""
    try:
        leaders_data = await get_leaderboard_data()
        leaders_text = LEADERBOARD_MENU.format(**leaders_data)

        await callback.message.edit_text(
            leaders_text,
            reply_markup=get_leaderboard_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата в лидерборд: {e}")
        await callback.answer("Ошибка", show_alert=True)
