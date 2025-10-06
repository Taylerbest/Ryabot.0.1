# interfaces/telegram_bot/handlers/work.py
"""
Handler меню работ
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_work_keyboard():
    """Клавиатура работ - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_WORK_BREACH, callback_data="work_breach"),
         InlineKeyboardButton(text=BTN_WORK_EXPEDITION, callback_data="work_expedition")],
        [InlineKeyboardButton(text=BTN_WORK_CITY, callback_data="work_city"),
         InlineKeyboardButton(text=BTN_WORK_FARM, callback_data="work_farm")],
        [InlineKeyboardButton(text=BTN_WORK_FOREST, callback_data="work_forest"),
         InlineKeyboardButton(text=BTN_WORK_SEA, callback_data="work_sea")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_work_stats(user_id: int) -> dict:
    """Получить статистику работников"""
    # TODO: Получать реальные данные из БД
    return {
        "workers_total": 0,
        "builders_total": 0,
        "farmers_total": 0,
        "foresters_total": 0,
        "fishermen_total": 0,
        "cooks_total": 0,
        "doctors_total": 0,
        "scientists_total": 0,
        "teachers_total": 0,
        "q_soldiers_total": 0,
        "works_completed": 0,
        "anomaly_pool": 840000,
        "expedition_pool": 2730000,
        "work_rating": 0
    }


async def show_work_menu(message: Message):
    """Показать меню работ"""
    try:
        user_id = message.from_user.id

        # Получаем энергию и статистику
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy"],
            filters={"user_id": user_id},
            single=True
        )

        energy = user_data.get('energy', 0) if user_data else 0

        work_stats = await get_work_stats(user_id)
        work_stats['energy'] = energy

        # Формируем текст меню
        work_text = WORK_MENU.format(**work_stats)

        await message.answer(
            work_text,
            reply_markup=get_work_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка меню работ: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИКИ ЛОКАЦИЙ РАБОТ ===

@router.callback_query(F.data.startswith("work_"))
async def handle_work_location(callback: CallbackQuery):
    """Обработка локаций работ"""
    try:
        location = callback.data.split("_")[1]

        location_names = {
            "breach": "⚠️ БРЕШЬ",
            "expedition": "🏕 ВЫЛАЗКА",
            "city": "🏢 ГОРОД",
            "farm": "🏡 ФЕРМА",
            "forest": "🌲 ЛЕС",
            "sea": "🌊 МОРЕ"
        }

        location_name = location_names.get(location, "НЕИЗВЕСТНАЯ ЛОКАЦИЯ")

        await callback.message.edit_text(
            f"{location_name}\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_work")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка локации работ: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_work")
async def back_to_work(callback: CallbackQuery):
    """Возврат в меню работ"""
    try:
        user_id = callback.from_user.id

        # Получаем данные и показываем меню
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy"],
            filters={"user_id": user_id},
            single=True
        )

        energy = user_data.get('energy', 0) if user_data else 0

        work_stats = await get_work_stats(user_id)
        work_stats['energy'] = energy

        work_text = WORK_MENU.format(**work_stats)

        await callback.message.edit_text(
            work_text,
            reply_markup=get_work_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата в работы: {e}")
        await callback.answer("Ошибка", show_alert=True)
