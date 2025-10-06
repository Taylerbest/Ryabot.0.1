# interfaces/telegram_bot/handlers/farm.py
"""
Handler меню фермы
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_farm_keyboard():
    """Клавиатура фермы - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_FARM_HENHOUSE, callback_data="farm_henhouse"),
         InlineKeyboardButton(text=BTN_FARM_COWSHED, callback_data="farm_cowshed")],
        [InlineKeyboardButton(text=BTN_FARM_SHEEPFOLD, callback_data="farm_sheepfold"),
         InlineKeyboardButton(text=BTN_FARM_PIGSTY, callback_data="farm_pigsty")],
        [InlineKeyboardButton(text=BTN_FARM_APIARY, callback_data="farm_apiary"),
         InlineKeyboardButton(text=BTN_FARM_GARDEN, callback_data="farm_garden")],
        [InlineKeyboardButton(text=BTN_FARM_FORESTRY, callback_data="farm_forestry"),
         InlineKeyboardButton(text=BTN_FARM_FISHPOND, callback_data="farm_fishpond")],
        [InlineKeyboardButton(text=BTN_FARM_MINE, callback_data="farm_mine"),
         InlineKeyboardButton(text=BTN_FARM_VILLAGE, callback_data="farm_village")],
        [InlineKeyboardButton(text=BTN_FARM_QUANTUMLAB, callback_data="farm_quantumlab"),
         InlineKeyboardButton(text=BTN_FARM_STABLE, callback_data="farm_stable")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_farm_data(user_id: int) -> dict:
    """Получить данные фермы"""
    try:
        # TODO: Получать реальные данные из БД
        return {
            "farmer_id": f"L{user_id}",
            "total_area": 0,
            "lab_pool": 5250000,
            "farmer_rating": 0
        }
    except Exception as e:
        logger.error(f"Ошибка получения данных фермы: {e}")
        return {
            "farmer_id": f"L{user_id}",
            "total_area": 0,
            "lab_pool": 5250000,
            "farmer_rating": 0
        }


async def show_farm_menu(message: Message):
    """Показать меню фермы"""
    try:
        user_id = message.from_user.id

        farm_data = await get_farm_data(user_id)
        farm_text = FARM_MENU.format(**farm_data)

        await message.answer(
            farm_text,
            reply_markup=get_farm_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка меню фермы: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИКИ ПОСТРОЕК ФЕРМЫ ===

@router.callback_query(F.data.startswith("farm_"))
async def handle_farm_building(callback: CallbackQuery):
    """Обработка построек фермы"""
    try:
        building = callback.data.split("_")[1]

        building_names = {
            "henhouse": "🐔 КУРЯТНИК",
            "cowshed": "🐄 КОРОВНИК",
            "sheepfold": "🐑 ОВЧАРНЯ",
            "pigsty": "🐖 СВИНАРНИК",
            "apiary": "🐝 ПАСЕКА",
            "garden": "🪴 ОГОРОД",
            "forestry": "🌳 ЛЕСХОЗ",
            "fishpond": "🌊 РЫБНИК",
            "mine": "🪨 РУДНИК",
            "village": "🏘 ДЕРЕВНЯ",
            "quantumlab": "⚛️ КВАНТЛАБ",
            "stable": "🐎 КОНЮШНЯ"
        }

        building_name = building_names.get(building, "НЕИЗВЕСТНАЯ ПОСТРОЙКА")

        await callback.message.edit_text(
            f"{building_name}\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_farm")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка постройки фермы: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_farm")
async def back_to_farm(callback: CallbackQuery):
    """Возврат в меню фермы"""
    try:
        user_id = callback.from_user.id

        farm_data = await get_farm_data(user_id)
        farm_text = FARM_MENU.format(**farm_data)

        await callback.message.edit_text(
            farm_text,
            reply_markup=get_farm_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата в ферму: {e}")
        await callback.answer("Ошибка", show_alert=True)
