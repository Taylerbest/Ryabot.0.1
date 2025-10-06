# interfaces/telegram_bot/handlers/other.py
"""
Handler меню прочего
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *

router = Router()
logger = logging.getLogger(__name__)


def get_other_keyboard():
    """Клавиатура прочего - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_OTHER_CHAT, url="https://t.me/ryabot_island"),
         InlineKeyboardButton(text=BTN_OTHER_WIKI, url="https://telegra.ph/Ostrov-YABOT-Wiki-10-05")],
        [InlineKeyboardButton(text=BTN_OTHER_HISTORY, url="https://t.me/ryabot_history"),
         InlineKeyboardButton(text=BTN_OTHER_DESIGN, callback_data="other_design")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def show_other_menu(message: Message):
    """Показать меню прочего"""
    try:
        await message.answer(
            OTHER_MENU,
            reply_markup=get_other_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка меню прочего: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИК ДИЗАЙНА ===

@router.callback_query(F.data == "other_design")
async def other_design(callback: CallbackQuery):
    """Дизайн игры"""
    try:
        await callback.message.edit_text(
            f"🎨 *ДИЗАЙН ИГРЫ*\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_other")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка дизайна: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_other")
async def back_to_other(callback: CallbackQuery):
    """Возврат в меню прочего"""
    try:
        await callback.message.edit_text(
            OTHER_MENU,
            reply_markup=get_other_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата в прочее: {e}")
        await callback.answer("Ошибка", show_alert=True)
