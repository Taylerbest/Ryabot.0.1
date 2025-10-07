# interfaces/telegram_bot/handlers/town.py
"""
Handler меню города
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_town_keyboard():
    """Клавиатура города - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_TOWNHALL, callback_data="town_hall"),
         InlineKeyboardButton(text=BTN_MARKET, callback_data="town_market")],
        [InlineKeyboardButton(text=BTN_RYABANK, callback_data="town_ryabank"),
         InlineKeyboardButton(text=BTN_SHOP, callback_data="town_shop")],
        [InlineKeyboardButton(text=BTN_PAWNSHOP, callback_data="town_pawnshop"),
         InlineKeyboardButton(text=BTN_TAVERN, callback_data="town_tavern")],
        [InlineKeyboardButton(text=BTN_ACADEMY, callback_data="town_academy"),
         InlineKeyboardButton(text=BTN_FORTUNE, callback_data="town_fortune")],
        [InlineKeyboardButton(text=BTN_REALESTATE, callback_data="town_realestate"),
         InlineKeyboardButton(text=BTN_VETCENTER, callback_data="town_vetcenter")],
        [InlineKeyboardButton(text=BTN_CONSTRUCTION, callback_data="town_construction"),
         InlineKeyboardButton(text=BTN_HOSPITAL, callback_data="town_hospital")],
        [InlineKeyboardButton(text=BTN_QUANTUMHUB, callback_data="town_quantumhub"),
         InlineKeyboardButton(text=BTN_CEMETERY, callback_data="town_cemetery")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def show_town_menu(message: Message):
    """Показать меню города"""
    try:
        user_id = message.from_user.id

        # Получаем энергию пользователя
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy"],
            filters={"user_id": user_id},
            single=True
        )

        energy = user_data.get('energy', 0) if user_data else 0

        # Формируем текст меню
        town_text = TOWN_MENU.format(energy=energy)

        await message.answer(
            town_text,
            reply_markup=get_town_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка меню города: {e}")
        await message.answer(ERROR_GENERAL)


# === СПЕЦИАЛЬНЫЕ ОБРАБОТЧИКИ (ДО ОБЩЕГО) ===

@router.callback_query(F.data == "town_academy")
async def town_academy(callback: CallbackQuery):
    """Переход в академию"""
    try:
        from .academy import show_academy_menu
        await show_academy_menu(callback)
    except Exception as e:
        logger.error(f"❌ Ошибка академии: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "town_ryabank")
async def town_ryabank(callback: CallbackQuery):
    """Переход в Рябанк - обрабатывается в bank.py"""
    # Этот хендлер НЕ нужен, т.к. bank.py уже обрабатывает "town_ryabank"
    # Но если bank.py не перехватывает, оставляем заглушку
    logger.info(f"town_ryabank вызван из town.py (должен обрабатываться bank.py)")
    await callback.answer("Загрузка банка...", show_alert=False)


# === ОБЩИЙ ОБРАБОТЧИК ЗДАНИЙ ГОРОДА ===

@router.callback_query(F.data.startswith("town_"))
async def handle_town_building(callback: CallbackQuery):
    """Обработка остальных зданий города"""
    try:
        building = callback.data.split("_")[1]

        if building == 'quantumhub':
            return  # Обрабатывается в quantum_hub.py

        building_names = {
            "hall": "🏛 РАТУША",
            "market": "🛒 РЫНОК",
            "shop": "🏪 МАГАЗИН",
            "pawnshop": "💍 ЛОМБАРД",
            "tavern": "🍻 ТАВЕРНА",
            "fortune": "🎡 ФОРТУНА",
            "realestate": "🏞 НЕДВИЖКА",
            "vetcenter": "❤️‍🩹 ВЕТЦЕНТР",
            "construction": "🏗 СТРОЙСАМ",
            "hospital": "🏥 БОЛЬНИЦА",
            "cemetery": "🪦 КЛАДБИЩЕ"
        }

        building_name = building_names.get(building, "НЕИЗВЕСТНОЕ ЗДАНИЕ")

        await callback.message.edit_text(
            f"{building_name}\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_town")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка здания города: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_town")
async def back_to_town(callback: CallbackQuery):
    """Возврат в меню города"""
    try:
        user_id = callback.from_user.id

        # Получаем энергию пользователя
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy"],
            filters={"user_id": user_id},
            single=True
        )

        energy = user_data.get('energy', 0) if user_data else 0
        town_text = TOWN_MENU.format(energy=energy)

        await callback.message.edit_text(
            town_text,
            reply_markup=get_town_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата в город: {e}")
        await callback.answer("Ошибка", show_alert=True)
